"""Gemini function-calling tool definitions and dispatch. Spec §4.2 tool surface.

Only search_pois is fully wired in Slice 2. Other tools return graceful
"not yet available" responses so Gemini degrades without failing.
"""

import asyncio
import time

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.gemini import embedding_model, get_client
from app.clients.qdrant import COLLECTION_POIS
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.poi import POI

log = get_logger(__name__)


class ToolContext:
    def __init__(self, qdrant: AsyncQdrantClient, db: AsyncSession, user_id: str):
        self.qdrant = qdrant
        self.db = db
        self.user_id = user_id


def definitions() -> list[dict]:
    """Return Gemini-format function declarations for all tools."""
    return [
        {
            "name": "search_pois",
            "description": "Search for points of interest near a location. Finds places matching "
            "a natural-language query with optional vibe and category filters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language description of what to find. "
                        "e.g. 'quiet rooftop bar', 'street food for late night', "
                        "'scenic driving road with mountain views'.",
                    },
                    "lat": {"type": "number", "description": "Latitude of search center."},
                    "lng": {"type": "number", "description": "Longitude of search center."},
                    "radius_m": {
                        "type": "integer",
                        "description": "Search radius in meters. Default 5000.",
                    },
                    "vibe": {
                        "type": "string",
                        "description": "Filter by vibe tag. One of: food, nightlife, scenic, "
                        "activity, hidden, culture, shopping, nature, wellness.",
                    },
                    "limit": {"type": "integer", "description": "Max results. Default 10."},
                },
                "required": ["query", "lat", "lng"],
            },
        },
        {
            "name": "get_route",
            "description": "Get a route between two points. Not yet available — use your web "
            "search capability to suggest driving directions and estimated times instead.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_lat": {"type": "number"},
                    "from_lng": {"type": "number"},
                    "to_lat": {"type": "number"},
                    "to_lng": {"type": "number"},
                    "mode": {"type": "string", "description": "driving, walking, bicycling"},
                },
                "required": ["from_lat", "from_lng", "to_lat", "to_lng"],
            },
        },
        {
            "name": "nearby_along_route",
            "description": "Find POIs the user will pass in the next N minutes along their "
            "current route. Not yet available — use search_pois with their current location instead.",
            "parameters": {
                "type": "object",
                "properties": {
                    "horizon_min": {
                        "type": "integer",
                        "description": "Minutes ahead to check (typically 5-10).",
                    },
                },
                "required": ["horizon_min"],
            },
        },
        {
            "name": "get_event_today",
            "description": "Get events happening today near a location. Not yet available — "
            "use your web search capability to find live events, shows, and happenings instead.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number"},
                    "lng": {"type": "number"},
                    "radius_m": {"type": "integer"},
                },
                "required": ["lat", "lng"],
            },
        },
        {
            "name": "get_weather_now",
            "description": "Get current weather for a location. Not yet available — "
            "use your web search capability to check weather conditions instead.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number"},
                    "lng": {"type": "number"},
                },
                "required": ["lat", "lng"],
            },
        },
        {
            "name": "recall_user_instance",
            "description": "Check if the user has already reacted to a specific POI. "
            "Returns their sentiment and note if found.",
            "parameters": {
                "type": "object",
                "properties": {
                    "poi_id": {"type": "string", "description": "POI UUID to check."},
                },
                "required": ["poi_id"],
            },
        },
        {
            "name": "flag_poi_closed",
            "description": "Flag a POI as potentially closed or inaccurate. Forwarded to "
            "moderation queue. Not yet available.",
            "parameters": {
                "type": "object",
                "properties": {
                    "poi_id": {"type": "string"},
                    "evidence": {"type": "string", "description": "Why you think it's closed."},
                },
                "required": ["poi_id", "evidence"],
            },
        },
    ]


async def execute(
    tool_name: str,
    args: dict,
    ctx: ToolContext,
) -> dict:
    """Dispatch a tool call by name. Returns a result dict for Gemini."""
    settings = get_settings()
    timeout_ms = (
        settings.tool_route_timeout_ms
        if tool_name == "get_route"
        else settings.tool_default_timeout_ms
    )
    try:
        result = await asyncio.wait_for(
            _dispatch(tool_name, args, ctx), timeout=timeout_ms / 1000
        )
        return result
    except asyncio.TimeoutError:
        log.warning("tool_timeout", tool=tool_name, timeout_ms=timeout_ms)
        return {"error": "timeout", "message": f"Tool {tool_name} timed out."}
    except Exception as exc:
        log.error("tool_error", tool=tool_name, error=str(exc))
        return {"error": "unavailable", "message": str(exc)}


async def _dispatch(tool_name: str, args: dict, ctx: ToolContext) -> dict:
    if tool_name == "search_pois":
        return await _search_pois(args, ctx)
    if tool_name == "recall_user_instance":
        return await _recall_user_instance(args, ctx)
    if tool_name in {
        "get_route",
        "nearby_along_route",
        "get_event_today",
        "get_weather_now",
        "flag_poi_closed",
    }:
        return {
            "unavailable": True,
            "message": (
                f"The {tool_name} tool is not yet available. "
                f"Use your web search capability or general knowledge to answer instead."
            ),
        }
    return {"error": "unknown_tool", "message": f"Unknown tool: {tool_name}"}


async def _search_pois(args: dict, ctx: ToolContext) -> dict:
    """Hybrid search: embed query → Qdrant vector search with geo + payload filters."""
    query: str = args["query"]
    lat: float = args["lat"]
    lng: float = args["lng"]
    radius_m: int = args.get("radius_m", 5000)
    vibe: str | None = args.get("vibe")
    limit: int = min(args.get("limit", 10), 20)

    client = get_client()
    embed_start = time.monotonic()

    # Get query embedding
    embed_result = await client.aio.models.embed_content(
        model=embedding_model(),
        contents=query,
    )
    query_vector = embed_result.embeddings[0].values
    embed_ms = (time.monotonic() - embed_start) * 1000
    log.info("embedding_done", ms=round(embed_ms, 1), query_len=len(query))

    # Build Qdrant filter
    must_conditions = [
        FieldCondition(
            key="is_closed",
            match=False,  # type: ignore[call-overload]
        ),
    ]
    if vibe:
        must_conditions.append(FieldCondition(key="vibe_tags", match=MatchAny(any=[vibe])))

    qdrant_filter = Filter(must=must_conditions)

    # Vector search with geo pre-filter
    search_start = time.monotonic()
    results = await ctx.qdrant.search(
        collection_name=COLLECTION_POIS,
        query_vector=query_vector,
        query_filter=qdrant_filter,
        limit=limit * 2,  # oversample for geo filter
        with_payload=True,
    )
    search_ms = (time.monotonic() - search_start) * 1000
    log.info("qdrant_search_done", ms=round(search_ms, 1), hits=len(results))

    # Filter by geo radius in Postgres (more accurate than Qdrant geo)
    poi_ids = [r.id for r in results if r.id]
    if not poi_ids:
        return {"results": [], "message": "No matching places found nearby."}

    # Fetch POIs from Postgres with geo distance filter
    geo_start = time.monotonic()
    stmt = (
        select(
            POI.id,
            POI.name,
            POI.description,
            POI.category,
            POI.vibe_tags,
            POI.engagement_score,
            POI.freshness_score,
            text(
                "ST_Distance(location::geography, "
                f"ST_SetSRID(ST_MakePoint({lng}, {lat}), 4326)::geography)"
            ).label("distance_m"),
        )
        .where(
            POI.id.in_(poi_ids),
            text(
                "ST_DWithin(location::geography, "
                f"ST_SetSRID(ST_MakePoint({lng}, {lat}), 4326)::geography, {radius_m})"
            ),
        )
        .order_by(text("distance_m ASC"))
        .limit(limit)
    )
    result = await ctx.db.execute(stmt)
    rows = result.all()
    geo_ms = (time.monotonic() - geo_start) * 1000
    log.info("postgres_geo_filter_done", ms=round(geo_ms, 1), matches=len(rows))

    if not rows:
        return {"results": [], "message": "No matching places found within range."}

    return {
        "results": [
            {
                "id": str(row.id),
                "name": row.name,
                "description": row.description,
                "category": row.category,
                "vibe_tags": row.vibe_tags,
                "distance_m": round(float(row.distance_m)),
                "engagement_score": round(row.engagement_score, 2),
            }
            for row in rows
        ]
    }


async def _recall_user_instance(args: dict, ctx: ToolContext) -> dict:
    """Check if the user has already reacted to a specific POI."""
    from uuid import UUID

    from app.memory.instance import get_instance

    poi_id = UUID(args["poi_id"])
    instance = await get_instance(ctx.db, UUID(ctx.user_id), poi_id)

    if instance is None:
        return {"found": False, "message": "No memory of this place."}

    return {
        "found": True,
        "sentiment": instance.sentiment,
        "note": instance.note,
        "updated_at": instance.updated_at.isoformat() if instance.updated_at else None,
    }

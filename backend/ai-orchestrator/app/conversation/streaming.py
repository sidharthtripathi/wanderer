"""SSE streaming utilities. Formats events from the planner into
Server-Sent Events for the client. Spec §7.1 streaming response.
"""

from collections.abc import AsyncGenerator

import orjson
from fastapi.responses import StreamingResponse


def format_sse(event: dict) -> str:
    """Serialize an event dict to an SSE data line."""
    return f"data: {orjson.dumps(event).decode()}\n\n"


async def sse_generator(
    events: AsyncGenerator[dict, None],
) -> AsyncGenerator[str, None]:
    """Wrap an async generator of event dicts into an SSE text stream."""
    async for event in events:
        yield format_sse(event)
    yield format_sse({"type": "done"})


def stream_sse(events: AsyncGenerator[dict, None]) -> StreamingResponse:
    """Return a FastAPI StreamingResponse for SSE delivery.

    Usage:
        return stream_sse(planner.plan_turn(...))
    """
    return StreamingResponse(
        sse_generator(events),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

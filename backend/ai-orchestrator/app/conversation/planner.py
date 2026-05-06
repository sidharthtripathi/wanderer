"""Central conversation coordinator. Builds the system prompt (persona + memory +
mood + city), calls Gemini 2.5 Pro with tools, handles tool callbacks, and
streams tokens/events. Spec §7.1 conversation flow.
"""

from collections.abc import AsyncGenerator
from uuid import UUID

import orjson
from google import genai
from google.genai import types
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.gemini import get_client, planner_model
from app.clients.qdrant import get_qdrant
from app.conversation.tools import ToolContext, definitions, execute
from app.core.logging import get_logger
from app.memory.instance import instances_to_prompt_fragment
from app.memory.mood import MoodManager
from app.memory.profile import profile_to_prompt_fragment
from app.persona.base_prompt import build_persona_prompt
from app.persona.regional_flavor import get_flavor_pack

log = get_logger(__name__)


class ConversationPlanner:
    """Orchestrates one conversation turn: prompt assembly, Gemini call, tool dispatch."""

    def __init__(
        self,
        gemini_client: genai.Client,
        db_session: AsyncSession,
        redis_client: Redis,
    ):
        self.client = gemini_client
        self.db = db_session
        self.redis = redis_client
        self.mood_mgr = MoodManager()

    async def plan_turn(
        self,
        session_id: UUID,
        user_id: UUID,
        user_message: str,
        city_name: str | None,
        conversation_history: list[dict],
    ) -> AsyncGenerator[dict, None]:
        """Execute one conversation turn. Yields SSE event dicts.

        Yields:
            {"type": "token", "delta": "..."}
            {"type": "tool_call", "name": "...", "args": {...}}
            {"type": "tool_result", "name": "...", "status": "ok"|"error", "result": {...}}
            {"type": "error", "message": "..."}
        """
        # 1. Build system prompt
        system_prompt = await self._build_system_prompt(
            user_id=user_id,
            city_name=city_name or "this city",
            session_id=str(session_id),
        )

        # 2. Build contents list (Gemini format)
        contents = self._build_contents(system_prompt, conversation_history, user_message)

        # 3. Call Gemini with tools
        tool_config = types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(mode="AUTO")
        )
        tool_declarations = [
            types.FunctionDeclaration.model_validate(d) for d in definitions()
        ]
        tools = [
            types.Tool(function_declarations=tool_declarations),
            # Live web grounding via Gemini's built-in Google Search.
            # Spec §4.2: used for freshness and places not yet in our DB.
            types.Tool(google_search=types.GoogleSearch()),
        ]

        config = types.GenerateContentConfig(
            tools=tools,
            tool_config=tool_config,
            temperature=0.8,
            top_p=0.95,
            max_output_tokens=1024,
        )

        ctx = ToolContext(
            qdrant=get_qdrant(),
            db=self.db,
            user_id=str(user_id),
        )

        try:
            # Stream from Gemini — handles both text and function calls
            async for response in self.client.aio.models.generate_content_stream(
                model=planner_model(),
                contents=contents,
                config=config,
            ):
                if response.candidates is None:
                    continue

                for candidate in response.candidates:
                    if candidate.content is None:
                        continue

                    for part in candidate.content.parts:
                        if part.text:
                            yield {"type": "token", "delta": part.text}
                        elif part.function_call:
                            fc = part.function_call
                            yield {
                                "type": "tool_call",
                                "name": fc.name,
                                "args": fc.args if fc.args else {},
                            }

                            # Execute the tool
                            result = await execute(fc.name, fc.args or {}, ctx)
                            yield {
                                "type": "tool_result",
                                "name": fc.name,
                                "status": "error" if "error" in result else "ok",
                                "result": result,
                            }

                            # Feed tool result back to Gemini for continuation
                            # Build a function_response part and continue streaming
                            function_response = types.Part.from_function_response(
                                name=fc.name,
                                response=result,
                            )
                            # Rebuild contents with the tool call and response appended
                            follow_up_contents = self._build_contents_with_tool_result(
                                system_prompt,
                                conversation_history,
                                user_message,
                                fc,
                                result,
                            )
                            async for follow_up in self.client.aio.models.generate_content_stream(
                                model=planner_model(),
                                contents=follow_up_contents,
                                config=config,
                            ):
                                if follow_up.candidates:
                                    for c in follow_up.candidates:
                                        if c.content:
                                            for p in c.content.parts:
                                                if p.text:
                                                    yield {"type": "token", "delta": p.text}

        except Exception as exc:
            log.error("planner_turn_failed", error=str(exc))
            yield {"type": "error", "message": "I lost my train of thought. Try again?"}

    async def _build_system_prompt(
        self,
        user_id: UUID,
        city_name: str,
        session_id: str,
    ) -> str:
        """Assemble the full system prompt from persona + memory fragments."""
        flavor_pack = get_flavor_pack(city_name)

        parts = [
            build_persona_prompt(city_name=city_name, flavor_pack=flavor_pack),
        ]

        # Profile memory
        profile_fragment = await profile_to_prompt_fragment(self.db, user_id)
        if profile_fragment:
            parts.append(f"\n{profile_fragment}")

        # Instance memory (for nearby POIs — pass empty for now, horizon handles this)
        # In Slice 5, this will filter against the GPS horizon

        # Mood
        mood_fragment = await self.mood_mgr.mood_to_prompt_fragment(self.redis, session_id)
        if mood_fragment:
            parts.append(f"\n{mood_fragment}")

        return "\n".join(parts)

    def _build_contents(
        self,
        system_prompt: str,
        history: list[dict],
        user_message: str,
    ) -> list[types.Content]:
        """Build Gemini contents list from system prompt, history, and new message."""
        contents = []

        # System prompt as first user-content turn
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=system_prompt)],
            )
        )

        # Conversation history
        for turn in history:
            role = turn.get("role", "user")
            text = turn.get("text", "")
            # Map to model role for history (only model, not system)
            if role == "agent" or role == "model":
                contents.append(
                    types.Content(
                        role="model",
                        parts=[types.Part.from_text(text=text)],
                    )
                )
            else:
                contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=text)],
                    )
                )

        # Current user message
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_message)],
            )
        )

        return contents

    def _build_contents_with_tool_result(
        self,
        system_prompt: str,
        history: list[dict],
        user_message: str,
        function_call,
        result: dict,
    ) -> list[types.Content]:
        """Build contents for the follow-up call after a tool result is available."""
        contents = self._build_contents(system_prompt, history, user_message)

        # Append model's function call
        contents.append(
            types.Content(
                role="model",
                parts=[
                    types.Part.from_function_call(
                        name=function_call.name,
                        args=function_call.args or {},
                    )
                ],
            )
        )

        # Append function response
        contents.append(
            types.Content(
                role="user",
                parts=[
                    types.Part.from_function_response(
                        name=function_call.name,
                        response=result,
                    )
                ],
            )
        )

        return contents

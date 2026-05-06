"""Session-only mood state. Lives in Redis for the session lifetime.

Current vibe, energy, hunger — discarded at session end (a one-line summary survives).
Spec §4.2 memory model.
"""

import orjson
from redis.asyncio import Redis

MOOD_KEY = "session:{sid}:mood"


class MoodManager:
    @staticmethod
    def _key(session_id: str) -> str:
        return MOOD_KEY.format(sid=session_id)

    async def get_mood(self, redis: Redis, session_id: str) -> dict:
        raw = await redis.get(self._key(session_id))
        if raw is None:
            return {}
        return orjson.loads(raw)

    async def update_mood(self, redis: Redis, session_id: str, tags: dict) -> None:
        """Merge tags into current mood. e.g. {'tired': True, 'hungry': 'looking for food'}."""
        current = await self.get_mood(redis, session_id)
        merged = {**current, **tags}
        # Remove keys set to None/False explicitly
        merged = {k: v for k, v in merged.items() if v}
        await redis.set(self._key(session_id), orjson.dumps(merged).decode())

    async def clear_mood(self, redis: Redis, session_id: str) -> None:
        await redis.delete(self._key(session_id))

    async def mood_to_prompt_fragment(self, redis: Redis, session_id: str) -> str:
        mood = await self.get_mood(redis, session_id)
        if not mood:
            return ""
        tags = ", ".join(f"{k}: {v}" if v is not True else k for k, v in mood.items())
        return f"Current vibe: {tags}."

"""Rolling 30-60 minute route horizon. Slice 2 stub — full implementation in Slice 5.

In Slice 2, the horizon is implicit: the LLM conversationally suggests nearby POIs.
Full route-aware horizon (GPS-driven, with narration triggers) arrives in Slice 5
when realtime-edge and the Android foreground service are built.
"""


class HorizonPlanner:
    """Stub horizon planner. Returns empty — conversation handles suggestions for now."""

    async def get_current_horizon(self, session_id: str) -> list[dict]:
        return []

    async def rebuild_horizon(
        self,
        session_id: str,
        user_lat: float,
        user_lng: float,
        city_id: str | None = None,
    ) -> list[dict]:
        return []

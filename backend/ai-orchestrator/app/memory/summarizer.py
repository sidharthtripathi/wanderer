"""End-of-session memory extraction. Calls Gemini 2.5 Flash for summarization
and high-confidence preference extraction. Spec §4.2 memory model.

Profile updates only happen when confidence is high (3+ consistent signals).
"""

from google import genai

from app.clients.gemini import narration_model
from app.core.logging import get_logger

log = get_logger(__name__)

SUMMARY_PROMPT = """Summarize this wandering session. What did the user enjoy?
What places did they react to (positively or negatively)? What preferences emerged?
Keep it 2-3 sentences. Use the user's language."""

PROFILE_EXTRACTION_PROMPT = """Based on this conversation, identify any clear user preferences
that appeared 3+ times across the session. Only extract preferences, not one-off comments.

Return a JSON object of key-value pairs. Examples:
  {"dietary": "vegetarian", "pace": "relaxed", "budget": "mid"}
  {"dislikes_loud_nightlife": true, "prefers_hill_drives": true}

If no preference appears with high confidence, return an empty object: {}.

IMPORTANT: Do NOT extract:
- Things the user disliked once (that's instance memory, not profile)
- Vague or ambiguous preferences
- Anything not directly observable from the conversation

Return ONLY the JSON object, nothing else."""


async def generate_session_summary(
    client: genai.Client,
    conversation_turns: list[dict],
) -> str:
    """Call Gemini 2.5 Flash to produce a 2-3 sentence session summary."""
    if not conversation_turns:
        return "Empty session."

    transcript = _format_transcript(conversation_turns)
    prompt = f"{SUMMARY_PROMPT}\n\nConversation:\n{transcript}"

    try:
        response = await client.aio.models.generate_content(
            model=narration_model(),
            contents=prompt,
        )
        return response.text.strip()
    except Exception as exc:
        log.error("summary_generation_failed", error=str(exc))
        return "Session completed."


async def extract_profile_updates(
    client: genai.Client,
    conversation_turns: list[dict],
    existing_profile: dict,
) -> dict:
    """Call Gemini to extract high-confidence preferences from this session.

    Only returns preferences that appeared 3+ times across turns.
    Returns {} if nothing meets the threshold.
    """
    if len(conversation_turns) < 3:
        return {}

    transcript = _format_transcript(conversation_turns)
    prompt = (
        f"{PROFILE_EXTRACTION_PROMPT}\n\n"
        f"Existing profile: {existing_profile or 'empty'}\n\n"
        f"Conversation:\n{transcript}"
    )

    try:
        response = await client.aio.models.generate_content(
            model=narration_model(),
            contents=prompt,
        )
        import orjson

        result = orjson.loads(response.text.strip())
        if not isinstance(result, dict):
            return {}
        return result
    except Exception as exc:
        log.error("profile_extraction_failed", error=str(exc))
        return {}


def _format_transcript(turns: list[dict]) -> str:
    lines = []
    for turn in turns:
        role = turn.get("role", "unknown")
        text = turn.get("text", "")
        lines.append(f"{role}: {text}")
    return "\n".join(lines)

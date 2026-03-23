"""Prompts for vision analysis and story generation."""

from __future__ import annotations

VISION_SYSTEM = (
    "You analyze photographs. Reply with a single JSON object only — no markdown fences, "
    "no text before or after the JSON, no explanations. If uncertain about a field, use an "
    "empty string or an empty array for that field."
)

VISION_USER = """Analyze the image and describe the scene.

Your entire reply must be valid JSON and nothing else. Use exactly this shape (values are examples):

{
  "summary": "...",
  "objects": ["..."],
  "mood": "...",
  "setting": "..."
}

Field rules:
- "summary": 2-4 short sentences in English about what is happening.
- "objects": array of strings — main visible things or people (up to 12); use [] if unclear.
- "mood": one short English phrase for the emotional tone; "" if unclear.
- "setting": one short English phrase for place/time context; "" if unclear.

Do not add keys. Do not wrap in markdown."""


def story_user_prompt(lang: str, vision_json: str) -> str:
    lang_name = {
        "ru": "Russian",
        "en": "English",
    }.get(lang.lower(), lang)
    return f"""Based on this structured scene description (JSON), write a short creative story.

Scene (JSON):
{vision_json}

Requirements:
- Write in {lang_name}.
- The story must be brief: aim for 500-800 characters (count characters, not words).
- Hard limit: never exceed 900 characters total. If you are close to the limit, stop at a natural sentence end.
- Original narrative inspired by the scene; do not repeat the JSON verbatim.
- No title line unless it fits naturally; prefer plain story text."""

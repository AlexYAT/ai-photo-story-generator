"""Prompts for vision analysis and story generation."""

from __future__ import annotations

VISION_SYSTEM = (
    "You analyze photographs and return strictly valid JSON matching the schema. "
    "Be concise and concrete."
)

VISION_USER = """Look at the image and describe the scene.

Return a JSON object with exactly these keys:
- "summary": string, 2-4 sentences in English describing what is happening
- "objects": array of strings, main visible objects or people (up to 12 items)
- "mood": string, emotional tone of the scene in English (one short phrase)
- "setting": string, where and when it likely takes place in English (one short phrase)

No markdown, no extra keys, no commentary outside JSON."""


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
- Length: between 500 and 900 characters inclusive (count characters, not words).
- Original narrative inspired by the scene; do not repeat the JSON verbatim.
- No title line unless it fits naturally; prefer plain story text."""

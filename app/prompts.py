"""Prompts for vision analysis and story generation."""

from __future__ import annotations

VISION_SYSTEM = (
    "You are a careful vision analysis assistant. "
    "Your job is to describe only what is visibly supported by the image. "
    "Do not guess hidden facts, identities, intentions, brand names, or relationships unless they are clearly visible. "
    "Return exactly one valid JSON object and nothing else. "
    "No markdown, no code fences, no commentary, no extra text before or after the JSON. "
    "If a field is uncertain, use an empty string or an empty array."
)

VISION_USER = """Analyze the image and describe the visible scene.

Your entire reply must be a single valid JSON object and nothing else.

Use exactly this schema:
{
  "summary": "...",
  "objects": ["..."],
  "mood": "...",
  "setting": "..."
}

Requirements:
- Output language: English.
- "summary": 2-4 short factual sentences describing clearly visible details.
- Include visible physical attributes (e.g., hair, face, clothing, objects, environment).
- "objects": list the main visible elements (e.g., person, face, hair, clothing, background, objects), up to 12.
- Be specific but only about what is directly visible.
- You may describe appearance (hair color, facial expression, lighting), but do NOT infer identity, profession, or hidden context.
- "mood": one short phrase based on visible expression or scene tone.
- "setting": describe visible environment if any (e.g., studio, office, outdoor), or "" if unclear.
- Do not invent facts.
- Do not add extra keys.
- Do not use markdown or explanations.
- If uncertain, leave fields empty rather than guessing."""


def story_user_prompt(lang: str, vision_json: str) -> str:
    lang_name = {
        "ru": "Russian",
        "en": "English",
    }.get(lang.lower(), lang)
    return f'''Based on this structured scene description (JSON), write one short creative story.

Scene (JSON):
{vision_json}

Requirements:
- Write in {lang_name}.
- Output only the story text.
- Target length: 500-800 characters.
- Hard limit: never exceed 900 characters.
- The story must stay grounded in visible details from the scene.
- Use concrete elements (appearance, environment, objects).
- Avoid abstract or philosophical reflections.
- Do not introduce major events not supported by the scene.
- No title unless it fits naturally.
- End at a natural sentence boundary.'''

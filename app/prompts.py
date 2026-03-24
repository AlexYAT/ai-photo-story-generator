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
  "setting": "...",
  "scene_type": "photo",
  "confidence": 0.85
}

Requirements:
- Output language: English for summary, mood, setting, and string fields.
- "summary": 2-4 short factual sentences describing clearly visible details.
- Include visible physical attributes (e.g., hair, face, clothing, objects, environment).
- "objects": list the main visible elements, up to 12.
- "mood": one short phrase based on visible expression or scene tone.
- "setting": visible environment if any, or "" if unclear.
- "scene_type": one of: "photo" (ordinary photograph), "screenshot" (UI, text-heavy screen, document, terminal), "collage" (many distinct tiles/stickers/overlapping elements), "low_info" (very sparse content, almost empty, almost no discernible subject), "other".
- "confidence": a number between 0 and 1 for how confident you are in the overall description (higher = clearer scene).
- Do not invent facts.
- Do not add extra keys.
- Do not use markdown or explanations.
- If uncertain, leave fields empty rather than guessing."""


def story_system_message(style: str) -> str:
    if style == "factual":
        return (
            "You are a precise factual writer. "
            "Write a short plain description of the scene based on the JSON. "
            "No metaphors, no literary flourishes, no storytelling embellishment. "
            "Target length: 500-800 characters. Hard limit: 900 characters. "
            "Do not add headings or meta-text. Do not repeat the JSON verbatim."
        )
    return (
        "You are a concise and grounded creative writer. "
        "Write a short, vivid story based on the scene JSON. "
        "Keep the narrative concrete and visually anchored. "
        "Use details from the scene (appearance, environment, objects). "
        "Target length: 500-800 characters. "
        "Hard limit: never exceed 900 characters. "
        "Avoid abstract философские рассуждения и обобщения. "
        "Do not add explanations, titles, or meta-text. "
        "Do not repeat the JSON verbatim."
    )


def story_user_prompt(lang: str, vision_json: str, style: str) -> str:
    lang_name = {
        "ru": "Russian",
        "en": "English",
    }.get(lang.lower(), lang)
    if style == "factual":
        style_block = (
            "Write strictly in plain descriptive language: no metaphors, no literary flourishes, no narrative drama."
        )
    else:
        style_block = (
            "Write in a vivid, literary storytelling style (still grounded in the scene)."
        )
    return f'''Based on this structured scene description (JSON), write one short text.

Scene (JSON):
{vision_json}

Style instruction:
- {style_block}

Requirements:
- Write in {lang_name}.
- Output only the text.
- Target length: 500-800 characters.
- Hard limit: never exceed 900 characters.
- The text must stay grounded in visible details from the scene.
- Use concrete elements (appearance, environment, objects).
- Avoid abstract or philosophical reflections unless style is creative and minimal.
- Do not introduce major events not supported by the scene.
- No title unless it fits naturally.
- End at a natural sentence boundary.'''

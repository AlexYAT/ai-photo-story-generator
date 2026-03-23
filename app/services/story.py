"""Short story generation from vision data."""

from __future__ import annotations

import logging
import re

from openai import APIError, OpenAI

from app.config import Settings
from app.prompts import story_user_prompt

logger = logging.getLogger(__name__)


def _count_chars(text: str) -> int:
    return len(text)


def generate_story(
    settings: Settings,
    client: OpenAI,
    vision: dict,
    lang: str,
) -> str:
    import json

    vision_json = json.dumps(vision, ensure_ascii=False)
    user = story_user_prompt(lang, vision_json)

    logger.info("Generating story text")
    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "You write vivid short fiction. Follow length constraints exactly.",
                },
                {"role": "user", "content": user},
            ],
            temperature=0.85,
        )
    except APIError as exc:
        raise RuntimeError(
            f"OpenAI story generation API error: {exc.message or str(exc)}"
        ) from exc

    text = (response.choices[0].message.content or "").strip()
    if not text:
        raise RuntimeError("OpenAI returned an empty story.")

    # Strip accidental character-count annotations from the model
    text = re.sub(r"^\s*\(\d+\s*characters?\)\s*", "", text, flags=re.IGNORECASE)

    n = _count_chars(text)
    if n < 500 or n > 900:
        logger.warning(
            "Story length %s is outside 500-900; keeping model output as-is.",
            n,
        )

    return text

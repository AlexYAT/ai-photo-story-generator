"""Short story generation from vision data."""

from __future__ import annotations

import json
import logging
import re

from openai import APIError, OpenAI

from app.config import Settings
from app.prompts import story_system_message, story_user_prompt

logger = logging.getLogger(__name__)

STORY_TARGET_MIN = 500
STORY_TARGET_MAX = 800
STORY_HARD_MAX = 900


def _count_chars(text: str) -> int:
    return len(text)


def _trim_to_hard_max(text: str, max_len: int = STORY_HARD_MAX) -> str:
    if _count_chars(text) <= max_len:
        return text
    chunk = text[:max_len]
    cut = chunk.rfind(" ")
    if cut > max_len // 2:
        return text[:cut].rstrip()
    return chunk.rstrip()


def generate_story(
    settings: Settings,
    client: OpenAI,
    vision: dict,
    lang: str,
    style: str = "creative",
) -> str:
    vision_json = json.dumps(vision, ensure_ascii=False)
    user = story_user_prompt(lang, vision_json, style)
    system_msg = story_system_message(style)
    temp = 0.75 if style == "factual" else 0.85

    try:
        response = client.chat.completions.create(
            model=settings.openai_chat_model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user},
            ],
            temperature=temp,
        )
    except APIError as exc:
        raise RuntimeError(
            f"OpenAI story generation API error: {exc.message or str(exc)}"
        ) from exc

    text = (response.choices[0].message.content or "").strip()
    if not text:
        raise RuntimeError("OpenAI returned an empty story.")

    text = re.sub(r"^\s*\(\d+\s*characters?\)\s*", "", text, flags=re.IGNORECASE)

    before = _count_chars(text)
    text = _trim_to_hard_max(text, STORY_HARD_MAX)
    after = _count_chars(text)
    if after < before:
        logger.info("Story trimmed from %s to %s characters (hard max %s).", before, after, STORY_HARD_MAX)

    n = _count_chars(text)
    if n < STORY_TARGET_MIN or n > STORY_TARGET_MAX:
        logger.warning(
            "Story length %s is outside target range %s-%s (hard max %s applied).",
            n,
            STORY_TARGET_MIN,
            STORY_TARGET_MAX,
            STORY_HARD_MAX,
        )

    return text

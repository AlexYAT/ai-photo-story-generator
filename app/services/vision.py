"""Image analysis via OpenAI Vision."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from openai import APIError, OpenAI

from app.config import Settings
from app.prompts import VISION_SYSTEM, VISION_USER
from app.utils.image import encode_image, prepare_image

logger = logging.getLogger(__name__)


def _normalize_vision(data: dict[str, Any]) -> dict[str, Any]:
    raw_summary = data.get("summary", "")
    summary = "" if raw_summary is None else str(raw_summary)

    objects = data.get("objects", [])
    if not isinstance(objects, list):
        objects = []
    objects = [str(x) for x in objects if x is not None]

    raw_mood = data.get("mood", "")
    mood = "" if raw_mood is None else str(raw_mood)

    raw_setting = data.get("setting", "")
    setting = "" if raw_setting is None else str(raw_setting)

    return {
        "summary": summary,
        "objects": objects,
        "mood": mood,
        "setting": setting,
    }


def _parse_vision_text(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning(
            "Vision response was not valid JSON; storing raw text in summary only."
        )
        return {
            "summary": text,
            "objects": [],
            "mood": "",
            "setting": "",
        }

    if not isinstance(data, dict):
        logger.warning(
            "Vision JSON root is not an object; storing raw text in summary only."
        )
        return {
            "summary": text,
            "objects": [],
            "mood": "",
            "setting": "",
        }

    return _normalize_vision(data)


def analyze_image(
    settings: Settings,
    client: OpenAI,
    image_path: Path,
) -> dict[str, Any]:
    raw, mime = prepare_image(image_path)
    b64 = encode_image(raw)
    data_url = f"data:{mime};base64,{b64}"

    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": VISION_SYSTEM},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": VISION_USER},
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url},
                        },
                    ],
                },
            ],
            response_format={"type": "json_object"},
        )
    except APIError as exc:
        raise RuntimeError(
            f"OpenAI Vision API error: {exc.message or str(exc)}"
        ) from exc

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("OpenAI Vision returned an empty response.")

    return _parse_vision_text(content)

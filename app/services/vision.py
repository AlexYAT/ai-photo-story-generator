"""Image analysis via OpenAI Vision."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from openai import APIError, OpenAI

from app.config import Settings
from app.prompts import VISION_SYSTEM, VISION_USER
from app.utils.image import encode_image, prepare_image

logger = logging.getLogger(__name__)

ALLOWED_SCENE_TYPES = frozenset({"photo", "screenshot", "collage", "low_info", "other"})


def _clamp01(x: Any, default: float = 0.7) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, v))


def _refine_scene_heuristics(vision: dict[str, Any]) -> None:
    """Light heuristics to align scene_type/confidence with visible cues (in-place)."""
    summary = str(vision.get("summary", "")).lower()
    objects = vision.get("objects", [])
    n_obj = len(objects) if isinstance(objects, list) else 0
    st = str(vision.get("scene_type", "other"))
    if st not in ALLOWED_SCENE_TYPES:
        st = "other"
    conf = _clamp01(vision.get("confidence"), 0.7)

    texty = bool(
        re.search(
            r"\b(screenshot|interface|terminal|code|window|browser|document|spreadsheet|dashboard|ui)\b",
            summary,
        )
    )
    if texty and st in ("other", "photo"):
        st = "screenshot"
    if n_obj >= 8 and st in ("other", "photo"):
        st = "collage"
    if n_obj <= 1 and len(summary) < 100 and st not in ("screenshot", "collage"):
        st = "low_info"
        conf = min(conf, 0.42)

    vision["scene_type"] = st
    vision["confidence"] = conf


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

    st = str(data.get("scene_type", "other"))
    if st not in ALLOWED_SCENE_TYPES:
        st = "other"
    conf = _clamp01(data.get("confidence"), 0.7)

    vision = {
        "summary": summary,
        "objects": objects,
        "mood": mood,
        "setting": setting,
        "scene_type": st,
        "confidence": conf,
    }
    _refine_scene_heuristics(vision)
    return vision


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
            "scene_type": "other",
            "confidence": 0.5,
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
            "scene_type": "other",
            "confidence": 0.5,
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
            model=settings.openai_vision_model,
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

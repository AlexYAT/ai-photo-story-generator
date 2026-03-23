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


def analyze_image(
    settings: Settings,
    client: OpenAI,
    image_path: Path,
) -> dict[str, Any]:
    raw, mime = prepare_image(image_path)
    b64 = encode_image(raw)
    data_url = f"data:{mime};base64,{b64}"

    logger.info("Calling vision model for image analysis")
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

    text = response.choices[0].message.content
    if not text:
        raise RuntimeError("OpenAI Vision returned an empty response.")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "OpenAI Vision returned invalid JSON. Raw (truncated): "
            f"{text[:500]}..."
        ) from exc

    for key in ("summary", "objects", "mood", "setting"):
        if key not in data:
            raise RuntimeError(
                f"Vision JSON is missing required field '{key}'. Got keys: {list(data)}"
            )

    if not isinstance(data["objects"], list):
        raise RuntimeError("Vision JSON field 'objects' must be an array.")

    return {
        "summary": str(data["summary"]),
        "objects": [str(x) for x in data["objects"]],
        "mood": str(data["mood"]),
        "setting": str(data["setting"]),
    }

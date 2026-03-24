"""Shared vision → story → TTS → save pipeline for CLI and web."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from app.clients.openai_client import get_client
from app.config import load_settings
from app.services.story import generate_story
from app.services.tts import generate_speech
from app.services.vision import analyze_image
from app.utils.files import (
    FILENAME_RUN_META_JSON,
    make_run_dir,
    save_outputs,
)

logger = logging.getLogger(__name__)


def _low_info_message(lang: str) -> str:
    if str(lang).lower().startswith("ru"):
        return (
            "Изображение содержит мало визуальной информации. "
            "Невозможно построить содержательный рассказ."
        )
    return (
        "The image contains little visual information. "
        "A substantive narrative cannot be built."
    )


def _should_use_low_info_fallback(vision: dict[str, Any]) -> bool:
    if vision.get("scene_type") == "low_info":
        return True
    try:
        c = float(vision.get("confidence", 1))
    except (TypeError, ValueError):
        c = 1.0
    return c < 0.35


def run_pipeline(
    image_path: str | Path,
    output_dir: str | Path = "outputs",
    lang: str = "ru",
    style: str = "creative",
) -> dict[str, Any]:
    """
    Run vision → story → TTS → save artifacts.

    Returns a dict with paths, texts, timing, and run_meta (same shape as run_meta.json).
    Raises the same exceptions as the CLI on failure (FileNotFoundError, ValueError, OSError,
    RuntimeError, APIError from OpenAI).
    """
    settings = load_settings()
    client = get_client(settings)
    image_path = Path(image_path)
    output_dir = Path(output_dir)

    t0 = time.perf_counter()
    logger.info("Step 1: analyzing image")
    vision = analyze_image(settings, client, image_path)

    logger.info(
        "style=%s scene_type=%s confidence=%.2f",
        style,
        vision.get("scene_type"),
        float(vision.get("confidence") or 0),
    )

    if _should_use_low_info_fallback(vision):
        logger.info("Low-information scene: skipping story LLM; using short fallback text.")
        story = _low_info_message(lang)
    else:
        logger.info("Step 2: generating story")
        story = generate_story(settings, client, vision, lang, style)

    logger.info("Step 3: generating speech")
    audio = generate_speech(settings, client, story)

    input_resolved = str(image_path.expanduser().resolve())
    output_base = str(output_dir.expanduser().resolve())
    meta_base = {
        "input_image": input_resolved,
        "lang": lang,
        "output_dir": output_base,
        "vision_model": settings.openai_vision_model,
        "story_model": settings.openai_chat_model,
        "tts_model": settings.openai_tts_model,
        "style": style,
        "scene_type": vision.get("scene_type"),
        "confidence": vision.get("confidence"),
    }

    logger.info("Step 4: saving outputs")
    try:
        run_dir = make_run_dir(output_dir)
        created, elapsed = save_outputs(
            run_dir,
            vision,
            story,
            audio,
            meta_base,
            t0,
        )
    except OSError as exc:
        raise OSError(f"Failed to write output files: {exc}") from exc

    meta_path = run_dir / FILENAME_RUN_META_JSON
    run_meta = json.loads(meta_path.read_text(encoding="utf-8"))

    return {
        "run_dir": run_dir,
        "run_name": run_dir.name,
        "run_dir_str": str(run_dir),
        "created_files": created,
        "execution_time_sec": elapsed,
        "story_text": story,
        "vision": vision,
        "lang": lang,
        "style": style,
        "input_image": input_resolved,
        "output_dir_base": output_base,
        "run_meta": run_meta,
    }

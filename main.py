#!/usr/bin/env python3
"""CLI entry point for photo_to_story."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from openai import APIError

from app.clients.openai_client import get_client
from app.config import load_settings
from app.services.story import generate_story
from app.services.tts import generate_speech
from app.services.vision import analyze_image
from app.utils.files import make_run_dir, save_outputs

logger = logging.getLogger(__name__)


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze a photo, write a short story, and save audio.",
    )
    parser.add_argument(
        "--image",
        type=Path,
        required=True,
        help="Path to the input image file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Base directory for run folders (default: outputs).",
    )
    parser.add_argument(
        "--lang",
        default="ru",
        help="Story language code (default: ru).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    _setup_logging()
    args = _parse_args(argv)

    try:
        settings = load_settings()
    except ValueError as exc:
        logger.error("%s", exc)
        return 1

    client = get_client(settings)

    t0 = time.perf_counter()
    try:
        logger.info("Step 1: analyzing image")
        vision = analyze_image(settings, client, args.image)
        logger.info("Step 2: generating story")
        story = generate_story(settings, client, vision, args.lang)
        logger.info("Step 3: generating speech")
        audio = generate_speech(settings, client, story)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 2
    except OSError as exc:
        logger.error("Cannot read image file: %s", exc)
        return 2
    except RuntimeError as exc:
        logger.error("%s", exc)
        return 3
    except APIError as exc:
        logger.error(
            "OpenAI API error: %s",
            getattr(exc, "message", None) or str(exc),
        )
        return 3

    try:
        logger.info("Step 4: saving outputs")
        run_dir = make_run_dir(args.output_dir)
        save_outputs(run_dir, vision, story, audio)
    except OSError as exc:
        logger.error("Failed to write output files: %s", exc)
        return 4

    elapsed = time.perf_counter() - t0
    logger.info("Execution time: %.2f sec", elapsed)
    print(f"Execution time: {elapsed:.2f} sec", file=sys.stdout)

    logger.info("Done. Files saved under %s", run_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())

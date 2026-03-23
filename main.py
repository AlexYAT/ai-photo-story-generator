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
        help="Path to an image file (.png, .jpg, .jpeg, .webp).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Base directory for timestamped run folders (default: outputs).",
    )
    parser.add_argument(
        "--lang",
        default="ru",
        help="Story language code for the narrative text (default: ru).",
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
    except ValueError as exc:
        logger.error("%s", exc)
        return 5
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

    input_resolved = str(args.image.expanduser().resolve())
    output_base = str(args.output_dir.expanduser().resolve())
    meta_base = {
        "input_image": input_resolved,
        "lang": args.lang,
        "output_dir": output_base,
        "vision_model": settings.openai_vision_model,
        "story_model": settings.openai_chat_model,
        "tts_model": settings.openai_tts_model,
    }

    try:
        logger.info("Step 4: saving outputs")
        run_dir = make_run_dir(args.output_dir)
        created, elapsed = save_outputs(
            run_dir,
            vision,
            story,
            audio,
            meta_base,
            t0,
        )
    except OSError as exc:
        logger.error("Failed to write output files: %s", exc)
        return 4

    logger.info("Execution time: %.2f sec", elapsed)
    print(f"\nOutput directory:\n  {run_dir}\n", file=sys.stdout)
    print("Files created:", file=sys.stdout)
    for name in created:
        print(f"  - {name}", file=sys.stdout)
    print(f"\nExecution time: {elapsed:.2f} sec\n", file=sys.stdout)

    logger.info("Done. Files saved under %s", run_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())

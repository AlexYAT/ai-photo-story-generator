#!/usr/bin/env python3
"""CLI entry point for photo_to_story."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from openai import APIError

from app.pipeline import run_pipeline

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
    parser.add_argument(
        "--style",
        choices=("creative", "factual"),
        default="creative",
        help="Story mode: creative (narrative) or factual (plain description). Default: creative.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    _setup_logging()
    args = _parse_args(argv)

    try:
        result = run_pipeline(args.image, args.output_dir, args.lang, args.style)
    except ValueError as exc:
        if "OPENAI_API_KEY" in str(exc):
            logger.error("%s", exc)
            return 1
        logger.error("%s", exc)
        return 5
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 2
    except OSError as exc:
        if "Failed to write output files" in str(exc):
            logger.error("%s", exc)
            return 4
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

    run_dir = result["run_dir"]
    created = result["created_files"]
    elapsed = result["execution_time_sec"]
    vision = result["vision"]

    logger.info("Execution time: %.2f sec", elapsed)
    print(f"\nOutput directory:\n  {run_dir}\n", file=sys.stdout)
    print(
        f"Analysis: scene_type={vision.get('scene_type')} "
        f"confidence={vision.get('confidence')} style={result.get('style', 'creative')}",
        file=sys.stdout,
    )
    print("Files created:", file=sys.stdout)
    for name in created:
        print(f"  - {name}", file=sys.stdout)
    print(f"\nExecution time: {elapsed:.2f} sec\n", file=sys.stdout)

    logger.info("Done. Files saved under %s", run_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Output paths and file writes."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def make_run_dir(output_dir: Path) -> Path:
    """Create outputs/<timestamp>/ under the given base directory."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run = output_dir.expanduser().resolve() / stamp
    run.mkdir(parents=True, exist_ok=True)
    return run


def save_outputs(
    run_dir: Path,
    vision: dict,
    story_text: str,
    speech_bytes: bytes,
) -> None:
    """Write vision.json, story.txt, and story.mp3."""
    vision_path = run_dir / "vision.json"
    story_path = run_dir / "story.txt"
    audio_path = run_dir / "story.mp3"

    vision_path.write_text(
        json.dumps(vision, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    story_path.write_text(story_text, encoding="utf-8")
    audio_path.write_bytes(speech_bytes)

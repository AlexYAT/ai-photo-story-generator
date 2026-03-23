"""Output paths and file writes."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

# Fixed output artifact names (run folder)
FILENAME_VISION_JSON = "vision.json"
FILENAME_STORY_TXT = "story.txt"
FILENAME_STORY_MP3 = "story.mp3"
FILENAME_RUN_META_JSON = "run_meta.json"


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
    meta_base: dict,
    pipeline_started_at: float,
) -> tuple[list[str], float]:
    """Write vision.json, story.txt, story.mp3, run_meta.json. Returns filenames and elapsed seconds."""
    vision_path = run_dir / FILENAME_VISION_JSON
    story_path = run_dir / FILENAME_STORY_TXT
    audio_path = run_dir / FILENAME_STORY_MP3
    meta_path = run_dir / FILENAME_RUN_META_JSON

    vision_path.write_text(
        json.dumps(vision, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    story_path.write_text(story_text, encoding="utf-8")
    audio_path.write_bytes(speech_bytes)

    elapsed = time.perf_counter() - pipeline_started_at
    run_meta = {
        **meta_base,
        "execution_time_sec": round(elapsed, 3),
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "success",
    }
    meta_path.write_text(
        json.dumps(run_meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    names = [
        FILENAME_VISION_JSON,
        FILENAME_STORY_TXT,
        FILENAME_STORY_MP3,
        FILENAME_RUN_META_JSON,
    ]
    return names, elapsed

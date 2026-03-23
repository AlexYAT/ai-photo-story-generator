"""Image loading and encoding for the Vision API."""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path


def prepare_image(image_path: Path) -> tuple[bytes, str]:
    """
    Read image file and infer MIME type.
    Raises FileNotFoundError with a clear message if the path does not exist.
    """
    path = image_path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(
            f"Image file not found: {path}. Check the path passed to --image."
        )
    raw = path.read_bytes()
    mime, _ = mimetypes.guess_type(str(path))
    if not mime or not mime.startswith("image/"):
        mime = "image/jpeg"
    return raw, mime


def encode_image(raw: bytes) -> str:
    """Return base64-encoded image data for data URLs."""
    return base64.standard_b64encode(raw).decode("ascii")

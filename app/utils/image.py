"""Image loading and encoding for the Vision API."""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

ALLOWED_IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp"})


def prepare_image(image_path: Path) -> tuple[bytes, str]:
    """
    Read image file and infer MIME type.
    Raises FileNotFoundError if the path does not exist.
    Raises ValueError if the file extension is not supported.
    """
    path = image_path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(
            f"Image file not found: {path}. Check the path passed to --image."
        )
    suffix = path.suffix.lower()
    if suffix not in ALLOWED_IMAGE_SUFFIXES:
        allowed = ", ".join(sorted(ALLOWED_IMAGE_SUFFIXES))
        raise ValueError(
            f"Unsupported image format ({suffix!r}). Supported extensions: {allowed}."
        )
    raw = path.read_bytes()
    mime, _ = mimetypes.guess_type(str(path))
    if not mime or not mime.startswith("image/"):
        mime = "image/jpeg"
    return raw, mime


def encode_image(raw: bytes) -> str:
    """Return base64-encoded image data for data URLs."""
    return base64.standard_b64encode(raw).decode("ascii")

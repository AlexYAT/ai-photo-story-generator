"""OpenAI client factory."""

from __future__ import annotations

from openai import OpenAI

from app.config import Settings


def get_client(settings: Settings) -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key)

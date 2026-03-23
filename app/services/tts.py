"""Text-to-speech via OpenAI Audio API."""

from __future__ import annotations

import logging

from openai import APIError, OpenAI

from app.config import Settings

logger = logging.getLogger(__name__)


def generate_speech(settings: Settings, client: OpenAI, text: str) -> bytes:
    logger.info("Synthesizing speech")
    try:
        response = client.audio.speech.create(
            model=settings.openai_tts_model,
            voice=settings.openai_tts_voice,
            input=text,
        )
    except APIError as exc:
        raise RuntimeError(
            f"OpenAI TTS API error: {exc.message or str(exc)}"
        ) from exc

    return response.content

"""Text-to-speech via OpenAI Audio API."""

from __future__ import annotations

from openai import APIError, OpenAI

from app.config import Settings


def generate_speech(settings: Settings, client: OpenAI, text: str) -> bytes:
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

    audio = response.content
    if not audio:
        raise RuntimeError("OpenAI TTS returned empty audio; story.mp3 would be invalid.")
    return audio

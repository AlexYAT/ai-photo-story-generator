"""Load configuration from environment."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _env_str(name: str, default: str) -> str:
    raw = os.getenv(name)
    if raw is None:
        return default
    stripped = raw.strip()
    return stripped if stripped else default


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_model: str
    openai_tts_model: str
    openai_tts_voice: str


def load_settings() -> Settings:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "OPENAI_API_KEY is not set. Create a .env file (see .env.example) "
            "or export the variable in your environment."
        )
    return Settings(
        openai_api_key=key,
        openai_model=_env_str("OPENAI_MODEL", "gpt-4o"),
        openai_tts_model=_env_str("OPENAI_TTS_MODEL", "tts-1"),
        openai_tts_voice=_env_str("OPENAI_TTS_VOICE", "alloy"),
    )

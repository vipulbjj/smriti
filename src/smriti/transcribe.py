"""
Whisper transcription for voice notes received via WhatsApp.
Provider is selected via TRANSCRIPTION_PROVIDER env var:
  "groq"   — Groq whisper-large-v3 (free, 2K req/day)
  "openai" — OpenAI whisper-1 (paid)
"""

import io
from typing import Optional

from .config import config

_LANGUAGE_MAP = {"hindi": "hi", "english": "en", "punjabi": "pa"}


def transcribe(audio_bytes: bytes, language: str = "hindi") -> str:
    if config.transcription_provider == "openai" and config.openai_api_key:
        return _transcribe_openai(audio_bytes, language)
    # Default: Groq (free)
    from .ai import transcribe_groq
    return transcribe_groq(audio_bytes, language)


def _transcribe_openai(audio_bytes: bytes, language: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=config.openai_api_key)
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "voice_note.ogg"
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language=_LANGUAGE_MAP.get(language, "hi"),
    )
    return transcript.text.strip()

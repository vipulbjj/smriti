"""Whisper transcription for voice notes received via WhatsApp."""

import io
from typing import Optional

from openai import OpenAI

from .config import config

_LANGUAGE_MAP = {
    "hindi": "hi",
    "english": "en",
    "punjabi": "pa",
}

_openai: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _openai
    if _openai is None:
        _openai = OpenAI(api_key=config.openai_api_key)
    return _openai


def transcribe(audio_bytes: bytes, language: str = "hindi") -> str:
    whisper_lang = _LANGUAGE_MAP.get(language, "hi")
    client = _get_client()

    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "voice_note.ogg"  # Twilio sends OGG/Opus

    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language=whisper_lang,
    )
    return transcript.text.strip()

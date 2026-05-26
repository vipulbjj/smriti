"""
Whisper transcription for voice notes received via WhatsApp.
Provider is selected via TRANSCRIPTION_PROVIDER env var:
  "groq"        — Groq whisper-large-v3 (free, 2K req/day)
  "openai"      — OpenAI whisper-1 (paid)
  "huggingface" — self-hosted smriti-whisper microservice (HTTP, unlimited on a GPU)

The "huggingface" path is the reference example of how a vertical repo plugs in:
Smriti calls the deployed service over HTTP, selected purely by env var, with a
shared-secret key. If the service call fails it falls back to Groq so a voice note
is never silently lost. See docs/INTEGRATION_ARCHITECTURE.md.
"""

import io
import logging
from typing import Optional

from .config import config

logger = logging.getLogger(__name__)

_LANGUAGE_MAP = {"hindi": "hi", "english": "en", "punjabi": "pa"}


def transcribe(audio_bytes: bytes, language: str = "hindi") -> str:
    provider = config.transcription_provider
    if provider == "huggingface" and config.whisper_service_url:
        result = _transcribe_service(audio_bytes, language)
        if result is not None:
            return result
        logger.warning("smriti-whisper service failed — falling back to Groq")
    if provider == "openai" and config.openai_api_key:
        return _transcribe_openai(audio_bytes, language)
    # Default / fallback: Groq (free)
    from .ai import transcribe_groq
    return transcribe_groq(audio_bytes, language)


def _transcribe_service(audio_bytes: bytes, language: str) -> Optional[str]:
    """Call the self-hosted smriti-whisper microservice. Returns None on failure
    so the caller can fall back to a hosted provider."""
    import httpx

    try:
        resp = httpx.post(
            config.whisper_service_url.rstrip("/") + "/transcribe",
            files={"file": ("voice_note.ogg", audio_bytes, "audio/ogg")},
            data={"language": language, "x_api_key": config.whisper_api_key},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["text"].strip()
    except Exception:
        logger.exception("smriti-whisper service call failed")
        return None


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

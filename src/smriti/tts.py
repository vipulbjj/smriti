"""
Text-to-speech using gTTS (Google Translate TTS — completely free, no API key).
Falls back to ElevenLabs for higher quality if ELEVENLABS_API_KEY is set.
"""

import io
import logging
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import Response

from .config import config
from .db import Story, open_session

logger = logging.getLogger(__name__)
router = APIRouter()

_LANG_CODE = {"hindi": "hi", "english": "en", "punjabi": "pa"}


def generate_audio_gtts(text: str, language: str = "hindi") -> bytes:
    """Generate MP3 audio bytes using gTTS (free)."""
    from gtts import gTTS
    lang = _LANG_CODE.get(language, "hi")
    tts = gTTS(text=text, lang=lang, slow=False)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    return buf.getvalue()


def generate_audio_elevenlabs(text: str) -> Optional[bytes]:
    """Generate higher-quality audio via ElevenLabs (10K chars/month free)."""
    if not config.elevenlabs_api_key:
        return None
    try:
        import httpx
        # Rachel voice — warm, clear
        voice_id = "21m00Tcm4TlvDq8ikWAM"
        resp = httpx.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": config.elevenlabs_api_key,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.content
    except Exception:
        logger.exception("ElevenLabs TTS failed, falling back to gTTS")
        return None


def get_story_audio(story: Story, language: str) -> bytes:
    """Get audio for a story — tries ElevenLabs, falls back to gTTS."""
    text = story.enhanced_text or story.reply_text
    if not text:
        text = story.prompt_text
    audio = generate_audio_elevenlabs(text) if config.elevenlabs_api_key else None
    if audio is None:
        audio = generate_audio_gtts(text, language)
    return audio


@router.get("/media/audio/{story_id}", include_in_schema=False)
def serve_story_audio(story_id: int):
    """Stream TTS audio for a story. Generated on-demand — no storage needed."""
    from sqlmodel import select
    from .db import Grandparent

    with open_session() as session:
        story = session.get(Story, story_id)
        if not story:
            return Response(status_code=404)
        gp = session.get(Grandparent, story.grandparent_id)
        language = gp.language if gp else "english"

    audio = get_story_audio(story, language)
    return Response(content=audio, media_type="audio/mpeg")

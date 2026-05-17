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


_ELEVENLABS_VOICE = {
    "hindi": config.elevenlabs_voice_hindi,
    "english": config.elevenlabs_voice_english,
    "punjabi": config.elevenlabs_voice_punjabi,
}


def generate_audio_elevenlabs(text: str, language: str = "english") -> Optional[bytes]:
    """Generate higher-quality audio via ElevenLabs (10K chars/month free)."""
    if not config.elevenlabs_api_key:
        return None
    try:
        import httpx
        voice_id = _ELEVENLABS_VOICE.get(language, config.elevenlabs_voice_english)
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
    audio = generate_audio_elevenlabs(text, language) if config.elevenlabs_api_key else None
    if audio is None:
        audio = generate_audio_gtts(text, language)
    return audio


@router.get("/media/audio/{story_id}", include_in_schema=False)
def serve_story_audio(story_id: int):
    """Stream TTS audio for a story. Cached in story.audio_data after first generation."""
    from .db import Grandparent, update_story_fields

    with open_session() as session:
        story = session.get(Story, story_id)
        if not story:
            return Response(status_code=404)
        if story.audio_data:
            return Response(content=story.audio_data, media_type="audio/mpeg")
        gp = session.get(Grandparent, story.grandparent_id)
        language = gp.language if gp else "english"

    audio = get_story_audio(story, language)
    update_story_fields(story_id, audio_data=audio)
    return Response(content=audio, media_type="audio/mpeg")


@router.get("/media/photo/{story_id}", include_in_schema=False)
def serve_story_photo(story_id: int):
    """Serve a photo attached to a story. Bytes stored permanently in story.photo_data."""
    with open_session() as session:
        story = session.get(Story, story_id)
        if not story or not story.photo_data:
            return Response(status_code=404)
        return Response(content=story.photo_data, media_type="image/jpeg")

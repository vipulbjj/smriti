"""
AI features powered by Groq (free tier):
  - Whisper transcription (whisper-large-v3, 2K req/day free)
  - Story enhancement (llama-3.1-8b-instant, 14.4K req/day free)
  - Story digest summary for grandchild
"""

import io
import logging
from typing import Optional

from .config import config

logger = logging.getLogger(__name__)

_LANG_CODE = {"hindi": "hi", "english": "en", "punjabi": "pa"}

_ENHANCE_SYSTEM = {
    "hindi": (
        "तुम एक सहृदय और कुशल लेखक हो। दादा या नानी की बात को सुंदर, प्रवाहमयी हिंदी में लिखो। "
        "उनकी आवाज़ और भावना बनाए रखो। कोई नई जानकारी मत जोड़ो। दो-तीन पैराग्राफ में लिखो।"
    ),
    "english": (
        "You are a compassionate editor. Polish the grandparent's words into warm, flowing prose "
        "while preserving their voice. Do not add information not in the original. 2-3 paragraphs max."
    ),
    "punjabi": (
        "ਤੁਸੀਂ ਇੱਕ ਸਹਿਰਦੀ ਲੇਖਕ ਹੋ। ਦਾਦਾ ਜਾਂ ਨਾਨੀ ਦੀ ਗੱਲ ਨੂੰ ਸੁੰਦਰ ਪੰਜਾਬੀ ਵਿੱਚ ਲਿਖੋ। "
        "ਉਹਨਾਂ ਦੀ ਆਵਾਜ਼ ਅਤੇ ਭਾਵਨਾ ਬਣਾਈ ਰੱਖੋ। ਕੋਈ ਨਵੀਂ ਜਾਣਕਾਰੀ ਨਾ ਜੋੜੋ।"
    ),
}

_DIGEST_SYSTEM = (
    "You are a warm family storyteller. Write a short (3-4 sentences) digest of a grandparent's "
    "story for their grandchild. Use second person ('Your {name} shared...'). Be warm and specific."
)


def _get_groq():
    try:
        from groq import Groq
        return Groq(api_key=config.groq_api_key)
    except ImportError:
        raise RuntimeError("groq package not installed")


def transcribe_groq(audio_bytes: bytes, language: str = "hindi") -> str:
    client = _get_groq()
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "voice_note.ogg"
    transcript = client.audio.transcriptions.create(
        model="whisper-large-v3",
        file=audio_file,
        language=_LANG_CODE.get(language, "hi"),
    )
    return transcript.text.strip()


def enhance_story(
    prompt_text: str,
    raw_reply: str,
    grandparent_name: str,
    language: str = "english",
) -> Optional[str]:
    """Polish raw voice-note text into flowing prose. Returns None if Groq unavailable."""
    if not config.groq_api_key:
        return None
    if not raw_reply or len(raw_reply.strip()) < 20:
        return None
    try:
        client = _get_groq()
        system = _ENHANCE_SYSTEM.get(language, _ENHANCE_SYSTEM["english"])
        user = f"Question: {prompt_text}\n\nRaw answer from {grandparent_name}: {raw_reply}"
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=600,
            temperature=0.65,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        logger.exception("Story enhancement failed for %s", grandparent_name)
        return None


def generate_digest(
    prompt_text: str,
    story_text: str,
    grandparent_name: str,
    grandchild_name: str,
) -> Optional[str]:
    """Generate a short story digest message for the grandchild."""
    if not config.groq_api_key:
        return None
    try:
        client = _get_groq()
        user = (
            f"Grandparent: {grandparent_name}\nGrandchild: {grandchild_name}\n"
            f"Question: {prompt_text}\nStory: {story_text}"
        )
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": _DIGEST_SYSTEM},
                {"role": "user", "content": user},
            ],
            max_tokens=200,
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        logger.exception("Digest generation failed")
        return None

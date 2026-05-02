"""
Video generation via Shotstack (free sandbox — watermarked).
Creates a story card video: warm background + text + optional narration audio.

Shotstack render is async: submit → get job_id → poll for URL.
"""

import logging
from typing import Optional

import httpx

from .config import config

logger = logging.getLogger(__name__)

_SANDBOX_URL = "https://api.shotstack.io/edit/stage"
_PROD_URL = "https://api.shotstack.io/edit/v1"

_BG_COLORS = {
    "hindi": "#FBF5EC",
    "english": "#F0F4FF",
    "punjabi": "#FFF5F0",
}

_TEXT_COLORS = {
    "hindi": "#1C1917",
    "english": "#1E3A5F",
    "punjabi": "#4A1942",
}


def _base_url() -> str:
    return _PROD_URL if config.shotstack_api_key and "prod" in config.shotstack_api_key else _SANDBOX_URL


def _headers() -> dict:
    return {"x-api-key": config.shotstack_api_key, "Content-Type": "application/json"}


def _truncate(text: str, max_chars: int = 280) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "…"


def submit_story_video(
    story_id: int,
    story_text: str,
    grandparent_name: str,
    week_number: int,
    language: str = "english",
    audio_url: Optional[str] = None,
) -> Optional[str]:
    """
    Submit a Shotstack render job. Returns job_id or None if unavailable.
    Call get_video_url(job_id) later to fetch the result.
    """
    if not config.shotstack_api_key:
        return None

    bg_color = _BG_COLORS.get(language, "#FBF5EC")
    text_color = _TEXT_COLORS.get(language, "#1C1917")
    excerpt = _truncate(story_text)

    clips = [
        # Warm background
        {
            "asset": {"type": "shape", "shape": "rectangle", "width": 1.0, "height": 1.0,
                      "fill": {"color": bg_color}},
            "start": 0, "length": 20, "position": "center",
        },
        # Week label
        {
            "asset": {
                "type": "title", "text": f"Week {week_number} · smriti",
                "style": "minimal", "color": "#B45309", "size": "x-small",
                "position": "top",
            },
            "start": 0, "length": 20,
            "transition": {"in": "fade"},
        },
        # Grandparent name
        {
            "asset": {
                "type": "title", "text": grandparent_name,
                "style": "minimal", "color": text_color, "size": "medium",
                "position": "topLeft",
            },
            "start": 0.5, "length": 19,
            "transition": {"in": "slideRight"},
        },
        # Story text
        {
            "asset": {
                "type": "title", "text": f'"{excerpt}"',
                "style": "minimal", "color": text_color, "size": "small",
                "position": "center",
            },
            "start": 1.5, "length": 18,
            "transition": {"in": "fade", "out": "fade"},
        },
        # Footer
        {
            "asset": {
                "type": "title", "text": "smriti · preserve your family's stories",
                "style": "minimal", "color": "#999999", "size": "x-small",
                "position": "bottom",
            },
            "start": 0, "length": 20,
        },
    ]

    timeline: dict = {
        "background": bg_color,
        "tracks": [{"clips": clips}],
    }

    if audio_url:
        timeline["soundtrack"] = {
            "src": audio_url,
            "effect": "fadeInFadeOut",
        }

    payload = {
        "timeline": timeline,
        "output": {"format": "mp4", "resolution": "hd", "fps": 24},
        "callback": None,
    }

    try:
        resp = httpx.post(
            f"{_base_url()}/render",
            headers=_headers(),
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        job_id = resp.json()["response"]["id"]
        logger.info("Shotstack job submitted: %s for story %d", job_id, story_id)
        return job_id
    except Exception:
        logger.exception("Shotstack submit failed for story %d", story_id)
        return None


def get_video_url(job_id: str) -> Optional[str]:
    """Poll Shotstack for a completed render. Returns URL or None if not ready/failed."""
    if not config.shotstack_api_key or not job_id:
        return None
    try:
        resp = httpx.get(
            f"{_base_url()}/render/{job_id}",
            headers=_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()["response"]
        status = data.get("status")
        if status == "done":
            return data.get("url")
        if status == "failed":
            logger.warning("Shotstack job %s failed: %s", job_id, data.get("error"))
        return None
    except Exception:
        logger.exception("Shotstack poll failed for job %s", job_id)
        return None

"""Twilio WhatsApp client — send messages and download media."""

import httpx
from typing import Optional
from twilio.rest import Client

from .config import config

_twilio: Optional[Client] = None


def _client() -> Client:
    global _twilio
    if _twilio is None:
        _twilio = Client(config.twilio_account_sid, config.twilio_auth_token)
    return _twilio


def send_message(to_phone: str, body: str) -> str:
    """Send a WhatsApp message. Returns the Twilio message SID."""
    to = f"whatsapp:{to_phone}" if not to_phone.startswith("whatsapp:") else to_phone
    msg = _client().messages.create(
        from_=config.twilio_whatsapp_from,
        to=to,
        body=body,
    )
    return msg.sid


def send_media_message(to_phone: str, body: str, media_url: str) -> str:
    """Send a WhatsApp message with a media attachment (audio, video, image)."""
    to = f"whatsapp:{to_phone}" if not to_phone.startswith("whatsapp:") else to_phone
    msg = _client().messages.create(
        from_=config.twilio_whatsapp_from,
        to=to,
        body=body,
        media_url=[media_url],
    )
    return msg.sid


def download_voice_note(media_url: str) -> bytes:
    """Download a voice note from Twilio media URL. Returns raw audio bytes."""
    with httpx.Client() as client:
        response = client.get(
            media_url,
            auth=(config.twilio_account_sid, config.twilio_auth_token),
            follow_redirects=True,
            timeout=30,
        )
        response.raise_for_status()
        return response.content

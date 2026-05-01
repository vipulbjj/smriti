"""
WhatsApp webhook — receives incoming messages from Twilio.

Twilio sends a POST to /webhook/whatsapp for every inbound message.
We:
  1. Identify the grandparent by phone number.
  2. If they sent a voice note, download + transcribe it.
  3. Store the story.
  4. Advance their prompt index.
  5. Reply with a brief acknowledgement.
"""

from fastapi import APIRouter, Form
from fastapi.responses import PlainTextResponse

from .db import (
    Language,
    Story,
    advance_prompt,
    get_grandparent_by_phone,
    save_story,
)
from .prompts import get_prompt
from .transcribe import transcribe
from .whatsapp import download_voice_note, send_message

router = APIRouter()

_ACK = {
    "hindi": "🙏 बहुत शुक्रिया। आपकी बात हमने सुरक्षित कर ली है।",
    "english": "🙏 Thank you. Your story has been saved.",
    "punjabi": "🙏 ਬਹੁਤ ਧੰਨਵਾਦ। ਤੁਹਾਡੀ ਗੱਲ ਸੁਰੱਖਿਅਤ ਕਰ ਲਈ ਹੈ।",
}

_COMPLETION = {
    "hindi": "🙏 आपकी सभी 52 कहानियाँ पूरी हो गई हैं। आपकी किताब जल्द तैयार होगी।",
    "english": "🙏 All 52 stories are complete. Your book will be ready soon.",
    "punjabi": "🙏 ਤੁਹਾਡੀਆਂ ਸਾਰੀਆਂ 52 ਕਹਾਣੀਆਂ ਪੂਰੀਆਂ ਹੋ ਗਈਆਂ ਹਨ। ਤੁਹਾਡੀ ਕਿਤਾਬ ਜਲਦੀ ਤਿਆਰ ਹੋਵੇਗੀ।",
}


@router.post("/webhook/whatsapp", response_class=PlainTextResponse)
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(default=""),
    NumMedia: str = Form(default="0"),
    MediaUrl0: str = Form(default=""),
    MediaContentType0: str = Form(default=""),
):
    # Strip "whatsapp:" prefix Twilio prepends
    phone = From.replace("whatsapp:", "")

    gp = get_grandparent_by_phone(phone)
    if not gp:
        # Unknown sender — ignore silently (could be a test message)
        return ""

    if not gp.active:
        send_message(phone, _COMPLETION.get(gp.language, _COMPLETION["english"]))
        return ""

    reply_text = Body.strip()
    voice_note_url = ""

    # Handle voice note
    if int(NumMedia) > 0 and "audio" in MediaContentType0:
        voice_note_url = MediaUrl0
        audio_bytes = download_voice_note(MediaUrl0)
        reply_text = transcribe(audio_bytes, language=gp.language)

    if not reply_text:
        return ""

    prompt_text = get_prompt(gp.prompt_index, Language(gp.language))

    story = Story(
        grandparent_id=gp.id,
        prompt_index=gp.prompt_index,
        prompt_text=prompt_text,
        reply_text=reply_text,
        voice_note_url=voice_note_url,
    )
    save_story(story)
    advance_prompt(gp.id)

    send_message(phone, _ACK.get(gp.language, _ACK["english"]))
    return ""

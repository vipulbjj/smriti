"""
WhatsApp webhook — receives incoming messages from Twilio.

Twilio sends a POST to /webhook/whatsapp for every inbound message.
We:
  1. Validate the Twilio signature.
  2. Deduplicate via MessageSid (guards against Twilio retries).
  3. Identify the grandparent by phone number.
  4. If they sent a voice note, download + transcribe it.
  5. Store the story.
  6. Advance their prompt index.
  7. Reply with an acknowledgement.
  8. Notify the grandchild when all 52 stories are complete.
"""

import logging

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import PlainTextResponse
from twilio.request_validator import RequestValidator

from .config import config
from .db import (
    Family,
    Language,
    Story,
    advance_prompt,
    get_grandparent_by_phone,
    open_session,
    save_story,
    story_exists_by_sid,
)
from .prompts import get_prompt
from .transcribe import transcribe
from .whatsapp import download_voice_note, send_message

logger = logging.getLogger(__name__)
router = APIRouter()

_ACK = {
    "hindi": "🙏 {name} जी, शुक्रिया। यह याद हमेशा के लिए सुरक्षित है।",
    "english": "🙏 Thank you, {name}. This memory is saved forever.",
    "punjabi": "🙏 ਧੰਨਵਾਦ, {name} ਜੀ। ਇਹ ਯਾਦ ਹਮੇਸ਼ਾ ਲਈ ਸੁਰੱਖਿਅਤ ਹੈ।",
}

_COMPLETION = {
    "hindi": "🙏 {name} जी, आपकी सभी 52 कहानियाँ पूरी हो गई हैं। आपकी किताब जल्द तैयार होगी।",
    "english": "🙏 {name}, all 52 stories are complete. Your book will be ready soon.",
    "punjabi": "🙏 {name} ਜੀ, ਤੁਹਾਡੀਆਂ ਸਾਰੀਆਂ 52 ਕਹਾਣੀਆਂ ਪੂਰੀਆਂ ਹੋ ਗਈਆਂ ਹਨ। ਤੁਹਾਡੀ ਕਿਤਾਬ ਜਲਦੀ ਤਿਆਰ ਹੋਵੇਗੀ।",
}

_VOICE_ERROR = {
    "hindi": "⚠️ आवाज़ नहीं सुन पाए। क्या आप लिखकर जवाब दे सकते हैं?",
    "english": "⚠️ Couldn't process the voice note. Could you please type your answer?",
    "punjabi": "⚠️ ਆਵਾਜ਼ ਨਹੀਂ ਸੁਣ ਸਕੇ। ਕੀ ਤੁਸੀਂ ਲਿਖ ਕੇ ਜਵਾਬ ਦੇ ਸਕਦੇ ਹੋ?",
}

_GRANDCHILD_NOTIFICATION = (
    "🎉 {grandparent_name} has completed all 52 stories on smriti! "
    "Their memories are ready to become a book. "
    "Run: python -m smriti.admin generate-book --family-id {family_id}"
)


async def _check_twilio_signature(request: Request) -> None:
    if not config.validate_twilio_signature:
        return
    signature = request.headers.get("X-Twilio-Signature", "")
    form_data = dict(await request.form())
    url = config.webhook_base_url.rstrip("/") + "/webhook/whatsapp"
    if not RequestValidator(config.twilio_auth_token).validate(url, form_data, signature):
        logger.warning("Invalid Twilio signature from %s", request.client)
        raise HTTPException(status_code=403)


@router.post(
    "/webhook/whatsapp",
    response_class=PlainTextResponse,
    dependencies=[Depends(_check_twilio_signature)],
    responses={403: {"description": "Invalid Twilio signature"}},
)
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(default=""),
    NumMedia: str = Form(default="0"),
    MediaUrl0: str = Form(default=""),
    MediaContentType0: str = Form(default=""),
    MessageSid: str = Form(default=""),
):
    try:
        phone = From.replace("whatsapp:", "")
        gp = get_grandparent_by_phone(phone)
        if not gp:
            return ""

        if not gp.active:
            send_message(
                phone,
                _COMPLETION.get(gp.language, _COMPLETION["english"]).format(name=gp.name),
            )
            return ""

        if story_exists_by_sid(MessageSid):
            logger.info("Duplicate MessageSid=%s from %s — ignoring", MessageSid, phone)
            return ""

        reply_text = Body.strip()
        voice_note_url = ""

        if int(NumMedia) > 0 and "audio" in MediaContentType0:
            voice_note_url = MediaUrl0
            try:
                audio_bytes = download_voice_note(MediaUrl0)
                reply_text = transcribe(audio_bytes, language=gp.language)
            except Exception:
                logger.exception("Voice note processing failed for %s", phone)
                send_message(phone, _VOICE_ERROR.get(gp.language, _VOICE_ERROR["english"]))
                return ""

        if not reply_text:
            return ""

        prompt_text = get_prompt(gp.prompt_index, Language(gp.language))
        story = Story(
            grandparent_id=gp.id,
            prompt_index=gp.prompt_index,
            prompt_text=prompt_text,
            reply_text=reply_text,
            voice_note_url=voice_note_url,
            twilio_message_sid=MessageSid,
        )
        save_story(story)
        advance_prompt(gp.id)

        send_message(
            phone,
            _ACK.get(gp.language, _ACK["english"]).format(name=gp.name),
        )

        # Notify the grandchild when all 52 stories are done
        updated_gp = get_grandparent_by_phone(phone)
        if updated_gp and not updated_gp.active:
            with open_session() as session:
                family = session.get(Family, updated_gp.family_id)
            if family and family.grandchild_phone:
                try:
                    send_message(
                        family.grandchild_phone,
                        _GRANDCHILD_NOTIFICATION.format(
                            grandparent_name=gp.name,
                            family_id=family.id,
                        ),
                    )
                    logger.info(
                        "Notified grandchild %s: %s completed all stories",
                        family.grandchild_phone,
                        gp.name,
                    )
                except Exception:
                    logger.exception("Failed to notify grandchild for family %s", family.id)

        return ""
    except Exception:
        logger.exception("Unhandled webhook error for From=%s", From)
        return ""

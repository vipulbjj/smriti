"""
WhatsApp webhook — receives incoming messages from Twilio.

Flow per message:
  1. Validate Twilio signature
  2. Deduplicate via MessageSid
  3. Identify grandparent by phone
  4. Handle media: voice note → transcribe, photo → store URL
  5. Save story, advance prompt index
  6. Fire AI enhancement + video generation in background
  7. ACK grandparent, optionally notify grandchild on completion
"""

import logging
from threading import Thread

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request
from fastapi.responses import PlainTextResponse
from twilio.request_validator import RequestValidator

from .commands import detect_command, handle_command
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
    update_story_fields,
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
    "🎉 {grandparent_name} has completed all 52 stories on smriti!\n\n"
    "View their memory timeline: {base_url}/family/{token}\n\n"
    "Their book is ready to generate."
)

_DIGEST_NOTE = {
    "hindi": "📖 इस हफ़्ते {name} जी ने एक यादगार बात साझा की:\n\n{digest}",
    "english": "📖 This week {name} shared a memory:\n\n{digest}",
    "punjabi": "📖 ਇਸ ਹਫ਼ਤੇ {name} ਜੀ ਨੇ ਇੱਕ ਯਾਦ ਸਾਂਝੀ ਕੀਤੀ:\n\n{digest}",
}


async def _check_twilio_signature(request: Request) -> None:
    if not config.validate_twilio_signature:
        return
    signature = request.headers.get("X-Twilio-Signature", "")
    form_data = dict(await request.form())
    url = config.webhook_base_url.rstrip("/") + "/webhook/whatsapp"
    if not RequestValidator(config.twilio_auth_token).validate(url, form_data, signature):
        logger.warning("Invalid Twilio signature from %s", request.client)
        raise HTTPException(status_code=403)


def _run_ai_pipeline(story_id: int, prompt_text: str, reply_text: str,
                     grandparent_name: str, language: str, week: int) -> None:
    """Background: enhance story text + submit Shotstack video job."""
    # 1. Story enhancement
    try:
        from .ai import enhance_story
        enhanced = enhance_story(prompt_text, reply_text, grandparent_name, language)
        if enhanced:
            update_story_fields(story_id, enhanced_text=enhanced)
            logger.info("Enhanced story %d", story_id)
    except Exception:
        logger.exception("AI enhancement failed for story %d", story_id)

    # 2. Video generation (if Shotstack configured)
    try:
        from .video import submit_story_video
        text_for_video = enhanced if enhanced else reply_text  # type: ignore[possibly-undefined]
        audio_url = f"{config.webhook_base_url}/media/audio/{story_id}"
        job_id = submit_story_video(
            story_id=story_id,
            story_text=text_for_video,
            grandparent_name=grandparent_name,
            week_number=week,
            language=language,
            audio_url=audio_url if config.shotstack_api_key else None,
        )
        if job_id:
            update_story_fields(story_id, video_job_id=job_id)
    except Exception:
        logger.exception("Video pipeline failed for story %d", story_id)


@router.post(
    "/webhook/whatsapp",
    response_class=PlainTextResponse,
    dependencies=[Depends(_check_twilio_signature)],
    responses={403: {"description": "Invalid Twilio signature"}},
)
async def whatsapp_webhook(
    background_tasks: BackgroundTasks,
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

        # Command detection — runs before story processing
        cmd = detect_command(Body)
        if cmd:
            logger.info("Command '%s' from %s", cmd, phone)
            handle_command(cmd, gp)
            return ""

        reply_text = Body.strip()
        voice_note_url = ""
        photo_url = ""
        photo_data: bytes | None = None
        num_media = int(NumMedia)

        if num_media > 0:
            content_type = MediaContentType0.lower()
            if "audio" in content_type:
                voice_note_url = MediaUrl0
                try:
                    audio_bytes = download_voice_note(MediaUrl0)
                    reply_text = transcribe(audio_bytes, language=gp.language)
                except Exception:
                    logger.exception("Voice note processing failed for %s", phone)
                    send_message(phone, _VOICE_ERROR.get(gp.language, _VOICE_ERROR["english"]))
                    return ""
            elif "image" in content_type:
                try:
                    photo_data = download_voice_note(MediaUrl0)  # same auth, same function
                    photo_url = f"{config.webhook_base_url}/media/photo/PENDING"  # set after save
                except Exception:
                    logger.exception("Photo download failed for %s — storing Twilio URL as fallback", phone)
                    photo_url = MediaUrl0  # fallback: use Twilio URL even if it expires
                if not reply_text:
                    reply_text = "📷"  # placeholder so the story is saved

        # Guard: don't save trivial greetings as memoir entries
        if not reply_text or (len(reply_text.strip()) < 15 and not photo_data and not voice_note_url):
            return ""

        prompt_text = get_prompt(gp.prompt_index, Language(gp.language))
        story = Story(
            grandparent_id=gp.id,
            prompt_index=gp.prompt_index,
            prompt_text=prompt_text,
            reply_text=reply_text,
            voice_note_url=voice_note_url,
            photo_url=photo_url,
            photo_data=photo_data,
            twilio_message_sid=MessageSid,
        )
        saved = save_story(story)

        # Update photo_url to point to our permanent endpoint now that we have story.id
        if photo_data and saved.id:
            from .db import update_story_fields
            photo_url = f"{config.webhook_base_url}/media/photo/{saved.id}"
            update_story_fields(saved.id, photo_url=photo_url)

        advance_prompt(gp.id)

        # AI enhancement + video are processed by /cron/process-pending (avoids Vercel timeout)

        send_message(
            phone,
            _ACK.get(gp.language, _ACK["english"]).format(name=gp.name),
        )

        # On completion: notify grandchild with timeline link
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
                            base_url=config.webhook_base_url,
                            token=family.timeline_token,
                        ),
                    )
                    logger.info("Notified grandchild %s — %s completed all stories",
                                family.grandchild_phone, gp.name)
                except Exception:
                    logger.exception("Failed to notify grandchild for family %s", family.id)
        else:
            # Send weekly digest to grandchild
            _send_digest_background(background_tasks, saved.id, gp, prompt_text, reply_text)

        return ""
    except Exception:
        logger.exception("Unhandled webhook error for From=%s", From)
        return ""


def _send_digest_background(background_tasks: BackgroundTasks, story_id: int,
                             gp, prompt_text: str, reply_text: str) -> None:
    """Send a short AI digest of the story to the grandchild (best-effort)."""
    background_tasks.add_task(
        _do_send_digest,
        story_id=story_id,
        grandparent_id=gp.id,
        family_id=gp.family_id,
        grandparent_name=gp.name,
        language=gp.language,
        prompt_text=prompt_text,
        reply_text=reply_text,
    )


def _do_send_digest(story_id: int, grandparent_id: int, family_id: int,
                    grandparent_name: str, language: str,
                    prompt_text: str, reply_text: str) -> None:
    try:
        from .ai import generate_digest
        with open_session() as session:
            from .db import Family as FamilyModel
            family = session.get(FamilyModel, family_id)
        if not family or not family.grandchild_phone:
            return
        digest = generate_digest(prompt_text, reply_text, grandparent_name, family.grandchild_name)
        if not digest:
            return
        msg = _DIGEST_NOTE.get(language, _DIGEST_NOTE["english"]).format(
            name=grandparent_name, digest=digest
        )
        send_message(family.grandchild_phone, msg)
        logger.info("Digest sent to grandchild for story %d", story_id)
    except Exception:
        logger.exception("Digest send failed for story %d", story_id)


@router.post("/webhook/status", response_class=PlainTextResponse, include_in_schema=False)
async def delivery_status(
    MessageSid: str = Form(default=""),
    MessageStatus: str = Form(default=""),
    To: str = Form(default=""),
    ErrorCode: str = Form(default=""),
):
    """Twilio delivery receipt callback. Set Status Callback URL in Twilio console."""
    if ErrorCode:
        logger.warning("Delivery failure SID=%s status=%s error=%s to=%s",
                       MessageSid, MessageStatus, ErrorCode, To)
    else:
        logger.info("Delivery SID=%s status=%s to=%s", MessageSid, MessageStatus, To)
    return ""

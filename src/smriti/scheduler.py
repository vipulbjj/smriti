"""
Scheduler jobs (used in non-serverless deployments).
On Vercel, /cron/send-prompts and /cron/send-reminders handle these instead.
"""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import select

from .config import config
from .db import Grandparent, Story, open_session, mark_prompted, get_grandparents_needing_reminder, update_story_fields
from .prompts import format_whatsapp_prompt, Language
from .program import SPRINT_LENGTH
from .whatsapp import send_message

logger = logging.getLogger(__name__)


def send_daily_prompts() -> int:
    """Send the next prompt once per day to participants ready for one."""
    sent = 0
    with open_session() as session:
        grandparents = session.exec(
            select(Grandparent).where(
                Grandparent.active == True,
                Grandparent.last_prompted_at == None,  # noqa: E711
                Grandparent.prompt_index < SPRINT_LENGTH,
            )
        ).all()
        gp_ids = [(gp.id, gp.name, gp.phone, gp.prompt_index, gp.language) for gp in grandparents]

    for gp_id, name, phone, prompt_index, language in gp_ids:
        try:
            message = format_whatsapp_prompt(
                index=prompt_index,
                language=Language(language),
                grandparent_name=name,
            )
            send_message(to_phone=phone, body=message)
            mark_prompted(gp_id)
            sent += 1
            logger.info("Sent sprint prompt %d/%d to %s (%s)", prompt_index + 1, SPRINT_LENGTH, name, phone)
        except Exception:
            logger.exception("Failed to send prompt to %s", name)

    logger.info("Daily sprint prompts: sent %d", sent)
    return sent


# Compatibility for existing admin scripts and integrations. New code should
# call ``send_daily_prompts``.
send_weekly_prompts = send_daily_prompts


def send_reminders() -> int:
    """Send a next-day nudge to grandparents who have not replied yet."""
    from .prompts import get_prompt

    candidates = get_grandparents_needing_reminder(days=1)
    sent = 0

    _REMINDER = {
        "hindi": (
            "🙏 {name} जी, बस एक याद दिलाना चाहते थे — आज का सवाल अभी भी "
            "आपका इंतज़ार कर रहा है:\n\n_{prompt}_\n\nकोई जल्दी नहीं है। 💙"
        ),
        "english": (
            "🙏 Hi {name}, just a gentle reminder — today's question is still "
            "waiting for you:\n\n_{prompt}_\n\nNo rush at all. 💙"
        ),
        "punjabi": (
            "🙏 {name} ਜੀ, ਬੱਸ ਇੱਕ ਯਾਦ ਦਿਵਾਉਣਾ — ਅੱਜ ਦਾ ਸਵਾਲ ਅਜੇ ਵੀ "
            "ਤੁਹਾਡੀ ਉਡੀਕ ਕਰ ਰਿਹਾ ਹੈ:\n\n_{prompt}_\n\nਕੋਈ ਜਲਦੀ ਨਹੀਂ। 💙"
        ),
    }

    for gp in candidates:
        try:
            prompt = get_prompt(gp.prompt_index, Language(gp.language))
            template = _REMINDER.get(gp.language, _REMINDER["english"])
            msg = template.format(name=gp.name, prompt=prompt)
            send_message(gp.phone, msg)
            sent += 1
            logger.info("Reminder sent to %s (%s)", gp.name, gp.phone)
        except Exception:
            logger.exception("Reminder failed for %s", gp.name)

    logger.info("Reminders: sent %d", sent)
    return sent


def process_pending_stories() -> int:
    """AI-enhance and submit Shotstack video jobs for stories not yet processed."""
    processed = 0
    with open_session() as session:
        pending = session.exec(
            select(Story).where(
                Story.reply_text != "",
                Story.enhanced_text == "",
                Story.video_job_id == "",
            )
        ).all()
        rows = [
            (s.id, s.prompt_text, s.reply_text, s.prompt_index,
             session.get(Grandparent, s.grandparent_id))
            for s in pending
        ]

    for story_id, prompt_text, reply_text, prompt_index, gp in rows:
        if not gp:
            continue
        enhanced = None
        try:
            from .ai import enhance_story
            enhanced = enhance_story(prompt_text, reply_text, gp.name, gp.language)
            if enhanced:
                update_story_fields(story_id, enhanced_text=enhanced)
                logger.info("Enhanced story %d", story_id)
        except Exception:
            logger.exception("AI enhancement failed for story %d", story_id)

        try:
            from .video import submit_story_video
            text_for_video = enhanced if enhanced else reply_text
            audio_url = f"{config.webhook_base_url}/media/audio/{story_id}"
            job_id = submit_story_video(
                story_id=story_id,
                story_text=text_for_video,
                grandparent_name=gp.name,
                week_number=prompt_index + 1,
                language=gp.language,
                audio_url=audio_url if config.shotstack_api_key else None,
            )
            if job_id:
                update_story_fields(story_id, video_job_id=job_id)
                logger.info("Video job submitted for story %d: %s", story_id, job_id)
        except Exception:
            logger.exception("Video pipeline failed for story %d", story_id)

        processed += 1

    logger.info("process_pending_stories: processed %d", processed)
    return processed


def process_pending_photos() -> int:
    """Run the story-from-image pipeline on photo stories not yet restored.

    For each story with photo bytes not yet restored/colorized:
      1. vision model reads the photo → description + story seed + questions
         (skipped if the row already has a description — e.g. one written
         synchronously by the webhook when the photo arrived)
      2. open models restore + colorize the photo (best-effort, optional)
      3. the elicitation questions are sent back to the grandparent on WhatsApp
         (skipped alongside the vision step, so a seed already described never
         gets a duplicate questions message)
    Each stage degrades independently; a missing provider never blocks the others.
    """
    processed = 0
    with open_session() as session:
        pending = session.exec(
            select(Story).where(
                Story.photo_data != None,          # noqa: E711 (SQL IS NOT NULL)
                Story.restored_photo_data == None, # noqa: E711 — not yet restored
            )
        ).all()
        rows = [
            (s.id, s.photo_data, s.prompt_text, s.prompt_index, s.photo_description,
             session.get(Grandparent, s.grandparent_id))
            for s in pending
        ]

    from .photo_story import describe_and_story, reconstruct_photo

    for story_id, photo_data, prompt_text, prompt_index, existing_description, gp in rows:
        if not gp or not photo_data:
            continue

        # Skip the vision call entirely for a seed already described (e.g. by the
        # webhook, synchronously, at photo-receive time) — avoids a wasted Groq
        # call and a duplicate description write / questions message.
        if not existing_description:
            result = describe_and_story(
                photo_bytes=photo_data,
                grandparent_name=gp.name,
                language=gp.language,
                prompt_text=prompt_text,
            )
            if result:
                update_story_fields(
                    story_id,
                    photo_description=result.description,
                    photo_story_text=result.story_seed,
                )
                logger.info("Photo story seed generated for story %d", story_id)
                if result.questions:
                    try:
                        send_message(gp.phone, result.questions_message(gp.name, gp.language))
                    except Exception:
                        logger.exception("Failed to send photo questions to %s", gp.name)

        try:
            restored, colorized = reconstruct_photo(photo_data)
            fields = {}
            if restored:
                fields["restored_photo_data"] = restored
            if colorized:
                fields["colorized_photo_data"] = colorized
            if fields:
                update_story_fields(story_id, **fields)
                logger.info("Photo reconstruction done for story %d (%s)",
                            story_id, ", ".join(fields))
        except Exception:
            logger.exception("Photo reconstruction failed for story %d", story_id)

        processed += 1

    logger.info("process_pending_photos: processed %d", processed)
    return processed


def start(run_immediately: bool = False) -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
    # Every morning at 9:00 AM IST — send the next sprint prompt.
    scheduler.add_job(
        send_daily_prompts,
        CronTrigger(hour=9, minute=0),
        id="daily_prompts",
        replace_existing=True,
    )
    # Every morning after the prompt pass — next-day reminder check.
    scheduler.add_job(
        send_reminders,
        CronTrigger(hour=10, minute=0),
        id="send_reminders",
        replace_existing=True,
    )
    # Every 15 minutes — AI enhance + Shotstack video submission
    scheduler.add_job(
        process_pending_stories,
        CronTrigger(minute="*/15"),
        id="process_pending",
        replace_existing=True,
    )
    scheduler.start()
    if run_immediately:
        send_daily_prompts()
    return scheduler

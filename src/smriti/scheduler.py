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
from .whatsapp import send_message

logger = logging.getLogger(__name__)


def send_weekly_prompts() -> int:
    """Send this week's prompt to every active grandparent. Returns count sent."""
    sent = 0
    with open_session() as session:
        grandparents = session.exec(
            select(Grandparent).where(Grandparent.active == True)
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
            logger.info("Sent prompt %d/52 to %s (%s)", prompt_index + 1, name, phone)
        except Exception:
            logger.exception("Failed to send prompt to %s", name)

    logger.info("Weekly prompts: sent %d", sent)
    return sent


def send_reminders() -> int:
    """Send 3-day nudge to grandparents who haven't replied yet."""
    from .prompts import get_prompt

    candidates = get_grandparents_needing_reminder(days=3)
    sent = 0

    _REMINDER = {
        "hindi": (
            "🙏 {name} जी, बस एक याद दिलाना चाहते थे — इस हफ़्ते का सवाल अभी भी "
            "आपका इंतज़ार कर रहा है:\n\n_{prompt}_\n\nकोई जल्दी नहीं है। 💙"
        ),
        "english": (
            "🙏 Hi {name}, just a gentle reminder — this week's question is still "
            "waiting for you:\n\n_{prompt}_\n\nNo rush at all. 💙"
        ),
        "punjabi": (
            "🙏 {name} ਜੀ, ਬੱਸ ਇੱਕ ਯਾਦ ਦਿਵਾਉਣਾ — ਇਸ ਹਫ਼ਤੇ ਦਾ ਸਵਾਲ ਅਜੇ ਵੀ "
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

    for story_id, prompt_text, reply_text, week, gp in rows:
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
                week_number=week,
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


def start(run_immediately: bool = False) -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
    # Monday 9:00 AM IST — send weekly prompts
    scheduler.add_job(
        send_weekly_prompts,
        CronTrigger(day_of_week="mon", hour=9, minute=0),
        id="weekly_prompts",
        replace_existing=True,
    )
    # Thursday 9:00 AM IST — 3-day reminder check
    scheduler.add_job(
        send_reminders,
        CronTrigger(day_of_week="thu", hour=9, minute=0),
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
        send_weekly_prompts()
    return scheduler

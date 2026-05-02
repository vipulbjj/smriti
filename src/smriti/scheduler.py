"""
Scheduler jobs (used in non-serverless deployments).
On Vercel, /cron/send-prompts and /cron/send-reminders handle these instead.
"""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import select

from .db import Grandparent, open_session, mark_prompted, get_grandparents_needing_reminder
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
    scheduler.start()
    if run_immediately:
        send_weekly_prompts()
    return scheduler

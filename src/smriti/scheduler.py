"""
Weekly prompt scheduler.
Every Monday at 9 AM IST, sends the next prompt to all active grandparents.
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import select

from .db import Grandparent, open_session
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

        for gp in grandparents:
            try:
                message = format_whatsapp_prompt(
                    index=gp.prompt_index,
                    language=Language(gp.language),
                    grandparent_name=gp.name,
                )
                send_message(to_phone=gp.phone, body=message)
                sent += 1
                logger.info("Sent prompt %d/52 to %s (%s)", gp.prompt_index + 1, gp.name, gp.phone)
            except Exception:
                logger.exception("Failed to send prompt to %s", gp.name)

    logger.info("Weekly prompts: sent %d", sent)
    return sent


def start(run_immediately: bool = False) -> BackgroundScheduler:
    """Start the background scheduler. Returns the scheduler instance."""
    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
    # Every Monday at 9:00 AM IST
    scheduler.add_job(
        send_weekly_prompts,
        CronTrigger(day_of_week="mon", hour=9, minute=0),
        id="weekly_prompts",
        replace_existing=True,
    )
    scheduler.start()

    if run_immediately:
        send_weekly_prompts()

    return scheduler

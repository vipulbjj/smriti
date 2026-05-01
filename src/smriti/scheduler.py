"""
Weekly prompt scheduler.
Every Monday at 9 AM IST, sends the next prompt to all active grandparents.
"""

from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import select

from .db import Grandparent, open_session
from .prompts import format_whatsapp_prompt, Language
from .whatsapp import send_message


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
                print(f"[scheduler] Sent prompt {gp.prompt_index + 1}/52 to {gp.name} ({gp.phone})")
            except Exception as exc:
                print(f"[scheduler] Failed to send to {gp.name}: {exc}")

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

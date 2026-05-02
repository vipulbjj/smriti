"""
Vercel Cron endpoints — called by Vercel's scheduler with Bearer auth.

  GET /cron/send-prompts   Monday 09:00 IST (03:30 UTC Mon)
  GET /cron/send-reminders Thursday 09:00 IST (03:30 UTC Thu)
  GET /cron/poll-videos    Hourly — check pending Shotstack renders
"""

import logging

from fastapi import APIRouter, HTTPException, Request

from .config import config
from .scheduler import send_weekly_prompts, send_reminders

logger = logging.getLogger(__name__)
router = APIRouter()


def _check_secret(request: Request) -> None:
    if not config.cron_secret:
        raise HTTPException(status_code=503, detail="CRON_SECRET not configured")
    if request.headers.get("Authorization") != f"Bearer {config.cron_secret}":
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/cron/send-prompts", include_in_schema=False)
def cron_send_prompts(request: Request):
    _check_secret(request)
    sent = send_weekly_prompts()
    logger.info("Cron send-prompts: sent %d", sent)
    return {"sent": sent}


@router.get("/cron/send-reminders", include_in_schema=False)
def cron_send_reminders(request: Request):
    _check_secret(request)
    sent = send_reminders()
    logger.info("Cron send-reminders: sent %d", sent)
    return {"sent": sent}


@router.get("/cron/poll-videos", include_in_schema=False)
def cron_poll_videos(request: Request):
    _check_secret(request)
    updated = _poll_pending_videos()
    return {"updated": updated}


def _poll_pending_videos() -> int:
    """Check Shotstack jobs that are submitted but not yet complete."""
    from sqlmodel import select
    from .db import Story, open_session, update_story_fields
    from .video import get_video_url

    updated = 0
    with open_session() as session:
        pending = session.exec(
            select(Story).where(
                Story.video_job_id != "",
                Story.video_url == "",
            )
        ).all()
        job_ids = [(s.id, s.video_job_id) for s in pending]

    for story_id, job_id in job_ids:
        url = get_video_url(job_id)
        if url:
            update_story_fields(story_id, video_url=url)
            updated += 1
            logger.info("Video ready for story %d: %s", story_id, url)

    return updated

"""
Vercel Cron endpoints — called by Vercel's scheduler with Bearer auth.

  GET /cron/send-prompts      Monday 09:00 IST (03:30 UTC Mon)
  GET /cron/send-reminders    Thursday 09:00 IST (03:30 UTC Thu)
  GET /cron/poll-videos       Hourly — check pending Shotstack renders
  GET /cron/process-pending   Every 15 min — AI enhance + submit video jobs
"""

import logging

from fastapi import APIRouter, HTTPException, Request

from .config import config
from .scheduler import (
    send_weekly_prompts,
    send_reminders,
    process_pending_stories,
    process_pending_photos,
)

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
    """Check Shotstack jobs that are submitted but not yet complete.
    When a video is ready, send it to the grandparent via WhatsApp."""
    from sqlmodel import select
    from .db import Story, Grandparent, open_session, update_story_fields
    from .video import get_video_url
    from .whatsapp import send_media_message

    updated = 0
    with open_session() as session:
        pending = session.exec(
            select(Story).where(
                Story.video_job_id != "",
                Story.video_url == "",
            )
        ).all()
        rows = []
        for s in pending:
            gp = session.get(Grandparent, s.grandparent_id)
            rows.append((s.id, s.video_job_id, s.prompt_index, gp.phone if gp else "", gp.language if gp else "english", gp.name if gp else ""))

    for story_id, job_id, prompt_index, phone, language, name in rows:
        url = get_video_url(job_id)
        if url:
            # Send first — only mark done if send succeeds (so failed sends retry next poll)
            if phone:
                try:
                    caption = {
                        "hindi": f"🎬 आपकी कहानी का वीडियो कार्ड — हफ़्ता {prompt_index + 1}/52",
                        "english": f"🎬 Your story card video is ready — Week {prompt_index + 1}/52",
                        "punjabi": f"🎬 ਤੁਹਾਡੀ ਕਹਾਣੀ ਦਾ ਵੀਡੀਓ — ਹਫ਼ਤਾ {prompt_index + 1}/52",
                    }.get(language, f"Week {prompt_index + 1}/52")
                    send_media_message(phone, caption, url)
                    logger.info("Video sent to %s for story %d", name, story_id)
                except Exception:
                    logger.exception("Failed to send video to %s — will retry next poll", name)
                    continue  # skip DB update so this story is retried next time
            update_story_fields(story_id, video_url=url)
            updated += 1
            logger.info("Video marked done for story %d: %s", story_id, url)

    return updated


@router.get("/cron/process-pending", include_in_schema=False)
def cron_process_pending(request: Request):
    _check_secret(request)
    processed = process_pending_stories()
    photos = process_pending_photos()
    logger.info("Cron process-pending: processed %d stories, %d photos", processed, photos)
    return {"processed": processed, "photos": photos}

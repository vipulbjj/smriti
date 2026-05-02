"""
Vercel Cron endpoint — replaces APScheduler for serverless deployments.

Vercel calls GET /cron/send-prompts every Monday at 09:00 IST (03:30 UTC)
and injects Authorization: Bearer <CRON_SECRET>.
"""

import logging

from fastapi import APIRouter, HTTPException, Request

from .config import config
from .scheduler import send_weekly_prompts

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/cron/send-prompts", include_in_schema=False)
def cron_send_prompts(request: Request):
    if not config.cron_secret:
        raise HTTPException(status_code=503, detail="CRON_SECRET not configured")
    if request.headers.get("Authorization") != f"Bearer {config.cron_secret}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    sent = send_weekly_prompts()
    logger.info("Cron triggered: sent %d prompts", sent)
    return {"sent": sent}

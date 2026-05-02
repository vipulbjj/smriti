"""FastAPI app — entry point."""

import logging
import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import Response

from .config import config
from .admin_web import router as admin_router
from .cron import router as cron_router
from .db import init_db
from .landing import router as landing_router
from .scheduler import start as start_scheduler
from .timeline import router as timeline_router
from .tts import router as tts_router
from .webhook import router as webhook_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

_scheduler = None
_IS_VERCEL = bool(os.environ.get("VERCEL"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler
    init_db()
    if not _IS_VERCEL:
        _scheduler = start_scheduler()
    yield
    if _scheduler:
        _scheduler.shutdown()


app = FastAPI(title="smriti", version="0.3.0", lifespan=lifespan)
app.include_router(landing_router)
app.include_router(admin_router)
app.include_router(webhook_router)
app.include_router(cron_router)
app.include_router(timeline_router)
app.include_router(tts_router)


@app.get("/health")
def health():
    if _IS_VERCEL:
        scheduler_status = "vercel-cron"
    elif _scheduler and _scheduler.running:
        scheduler_status = "running"
    else:
        scheduler_status = "stopped"

    return {
        "status": "ok",
        "service": "smriti",
        "version": "0.3.0",
        "scheduler": scheduler_status,
    }


@app.head("/health", include_in_schema=False)
def health_head():
    return Response(status_code=200)


if __name__ == "__main__":
    uvicorn.run("smriti.main:app", host="0.0.0.0", port=config.port, reload=False)

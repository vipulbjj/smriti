"""FastAPI app — entry point."""

import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI

from .config import config
from .db import init_db
from .scheduler import start as start_scheduler
from .webhook import router as webhook_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

_scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler
    init_db()
    _scheduler = start_scheduler()
    yield
    _scheduler.shutdown()


app = FastAPI(title="smriti", version="0.2.0", lifespan=lifespan)
app.include_router(webhook_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "smriti",
        "version": "0.2.0",
        "scheduler": "running" if _scheduler and _scheduler.running else "stopped",
    }


if __name__ == "__main__":
    uvicorn.run("smriti.main:app", host="0.0.0.0", port=config.port, reload=False)

"""FastAPI app — entry point."""

import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

from .config import config
from .db import init_db
from .scheduler import start as start_scheduler
from .webhook import router as webhook_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler = start_scheduler()
    yield
    scheduler.shutdown()


app = FastAPI(title="smriti", version="0.1.0", lifespan=lifespan)
app.include_router(webhook_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "smriti"}


if __name__ == "__main__":
    uvicorn.run("smriti.main:app", host="0.0.0.0", port=config.port, reload=False)

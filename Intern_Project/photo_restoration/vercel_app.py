"""
Lightweight FastAPI entrypoint for Vercel.

The full restoration pipeline (torch, transformers, diffusers, HF model
downloads) is not viable on Vercel serverless. Use Hugging Face Docker Spaces
(app.py + restore.py) for production restoration.
"""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

PLATFORM = "vercel"
DEPLOYMENT_MODE = os.environ.get("VERCEL_DEPLOYMENT_MODE", "stub")


class RestoreRequest(BaseModel):
    photo_url: HttpUrl


app = FastAPI(
    title="Photo Restoration (Vercel)",
    description=(
        "Health and API stub on Vercel. Full ML restoration runs on "
        "Hugging Face Docker Spaces (see README)."
    ),
)


@app.get("/")
async def health_check():
    return {
        "status": "ok",
        "platform": PLATFORM,
        "mode": DEPLOYMENT_MODE,
        "restore_available": False,
        "message": (
            "Vercel hosts this health/stub API only. Deploy the Docker image "
            "to Hugging Face Spaces for DDColor + Swin2SR restoration."
        ),
    }


@app.post("/restore")
async def restore_stub(request: RestoreRequest):
    raise HTTPException(
        status_code=503,
        detail={
            "error": "restore_not_available_on_vercel",
            "photo_url": str(request.photo_url),
            "reason": (
                "Photo restoration requires ~400MB+ Python deps (torch, "
                "transformers, diffusers), Hugging Face model downloads at "
                "startup, and 30–90+ seconds of CPU inference per image. "
                "Vercel serverless is limited to a 500MB bundle and is a "
                "poor fit for long-running CPU ML workloads."
            ),
            "recommended_platform": "Hugging Face Docker Spaces",
            "docs": "See README.md — sdk: docker, port 7860",
        },
    )

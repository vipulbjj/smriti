import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from secrets_utils import check_secrets, log_secrets_status
from webhook_router import router as webhook_router

# Load local .env during development (no-op if file is absent).
load_dotenv(encoding="utf-8-sig")

# Pre-create static directory so FastAPI StaticFiles doesn't crash on startup.
os.makedirs("static", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run startup and shutdown logic for the FastAPI application."""
    provider = os.getenv("WHATSAPP_PROVIDER", "").lower()

    log_secrets_status()

    if provider == "meta":
        print("[STARTUP] Using Meta WhatsApp adapter", flush=True)
    else:
        print("[STARTUP] Using Twilio adapter", flush=True)

    yield


app = FastAPI(lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Log validation failures with request context for easier debugging."""
    query_params = dict(request.query_params)
    print(
        f"[WEBHOOK] Request validation error on {request.method} {request.url.path}: "
        f"errors={exc.errors()}, query_params={query_params}",
        flush=True,
    )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


# Serve restored media files locally
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(webhook_router, prefix="")


@app.get("/")
async def root_check() -> dict[str, str]:
    """Return a simple root check response."""
    return {"status": "ok"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Return a simple health check response."""
    return {"status": "ok"}


@app.get("/debug/secrets")
async def debug_secrets() -> dict:
    """Return masked secret status for diagnostics (never exposes full tokens)."""
    return check_secrets()


from fastapi.responses import HTMLResponse

@app.get("/privacy", response_class=HTMLResponse)
async def privacy_policy():
    with open("privacy.html", "r", encoding="utf-8") as f:
        return f.read()
import os
import json
import asyncio
from typing import Any

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import PlainTextResponse, JSONResponse

from secrets_utils import mask_secret
from whatsapp_meta import (
    verify_webhook,
    send_message,
    send_media_message,
    download_voice_note,
)
from interview_engine import handle_incoming_voice_answer, start_interview
from state_store import get_state, init_db

router = APIRouter()

REQUIRED_GET_PARAMS = ("hub.mode", "hub.verify_token", "hub.challenge")

# Ensure SQLite interview_state table exists at import time.
init_db()


async def _post_with_retry(client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
    """Send a POST request with retry logic (up to 3 attempts, 2s delay)."""
    for attempt in range(1, 4):
        try:
            print(f"[RETRY] Sending POST to {url} (Attempt {attempt}/3)", flush=True)
            response = await client.post(url, timeout=60.0, **kwargs)
            response.raise_for_status()
            return response
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            print(f"[RETRY] Attempt {attempt} failed: {exc}", flush=True)
            if attempt == 3:
                raise exc
            await asyncio.sleep(2.0)
    raise RuntimeError(f"Request failed after 3 attempts: {url}")


async def handle_voice_note(sender: str, media_id: str) -> None:
    """Process voice note: download -> Whisper -> send text response."""
    print(f"[ROUTE-WORKER] Starting voice note handler for sender={sender}, media_id={mask_secret(media_id)}", flush=True)
    try:
        # Step 1: Download audio
        audio_bytes = await download_voice_note(media_id)
        print(f"[ROUTE-WORKER] Voice note downloaded, size={len(audio_bytes)} bytes", flush=True)

        # Step 2: Post to Whisper Service
        whisper_url = "https://bajajlakshit-whisper.hf.space/transcribe"
        files = {"file": ("voice.ogg", audio_bytes, "audio/ogg")}
        
        async with httpx.AsyncClient() as client:
            response = await _post_with_retry(client, whisper_url, files=files)
            
        data = response.json()
        transcript = data.get("text", "").strip()
        print(f"[ROUTE-WORKER] Whisper transcription complete: '{transcript[:100]}...'", flush=True)

        if not transcript:
            transcript = "Sorry, I couldn't hear any words in that voice note. Please try recording again! 🎙️"

        # Step 3: Reply to sender
        await send_message(sender, transcript)
        print(f"[ROUTE-WORKER] Sent transcription response to={sender}", flush=True)

    except Exception as exc:
        print(f"[ROUTE-WORKER] Error in handle_voice_note: {exc}", flush=True)
        try:
            await send_message(
                sender,
                "Sorry, we encountered an error while transcribing your voice note. Please try again later! 🌸"
            )
        except Exception as send_exc:
            print(f"[ROUTE-WORKER] Failed to send error message to user: {send_exc}", flush=True)


async def handle_image(sender: str, media_id: str) -> None:
    """Process image: download -> save locally -> Photo Restore -> send media response."""
    print(f"[ROUTE-WORKER] Starting image restoration handler for sender={sender}, media_id={mask_secret(media_id)}", flush=True)
    temp_path = f"static/temp_{media_id}.jpg"
    restored_path = f"static/restored_{media_id}.png"
    
    try:
        # Step 1: Download image bytes
        image_bytes = await download_voice_note(media_id)
        print(f"[ROUTE-WORKER] Downloaded image, size={len(image_bytes)} bytes", flush=True)

        # Step 2: Save raw image locally
        os.makedirs("static", exist_ok=True)
        with open(temp_path, "wb") as f:
            f.write(image_bytes)
        print(f"[ROUTE-WORKER] Saved original image to {temp_path}", flush=True)

        # Step 3: Call Photo Restoration Service
        base_url = os.getenv("ADAPTER_BASE_URL", "https://bajajlakshit-whatsapp-adapter.hf.space").rstrip("/")
        photo_url = f"{base_url}/{temp_path}"
        print(f"[ROUTE-WORKER] Requesting photo restoration for url={photo_url}", flush=True)

        restore_url = "https://bajajlakshit-photo-restoration.hf.space/restore"
        payload = {"photo_url": photo_url}
        
        async with httpx.AsyncClient() as client:
            response = await _post_with_retry(client, restore_url, json=payload)

        # Step 4: Save restored image
        with open(restored_path, "wb") as f:
            f.write(response.content)
        print(f"[ROUTE-WORKER] Saved restored image to {restored_path}", flush=True)

        # Step 5: Send restored image URL to user
        restored_public_url = f"{base_url}/{restored_path}"
        await send_media_message(sender, restored_public_url)
        print(f"[ROUTE-WORKER] Sent restored image to={sender}", flush=True)

    except Exception as exc:
        print(f"[ROUTE-WORKER] Error in handle_image: {exc}", flush=True)
        try:
            await send_message(
                sender,
                "Sorry, we encountered an error while restoring your photograph. Please check that the image is valid and try again! 🌸"
            )
        except Exception as send_exc:
            print(f"[ROUTE-WORKER] Failed to send error message to user: {send_exc}", flush=True)
    finally:
        # Step 6: Cleanup original file to save space
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                print(f"[ROUTE-WORKER] Cleaned up original temp image: {temp_path}", flush=True)
            except Exception as e:
                print(f"[ROUTE-WORKER] Failed to delete temp file {temp_path}: {e}", flush=True)


async def handle_text(sender: str, text: str) -> None:
    """Process text message: log and send acknowledgement reply."""
    print(f"[ROUTE-WORKER] Starting text handler for sender={sender}, text='{text[:100]}'", flush=True)
    try:
        reply = f"Thank you for sharing your thoughts: '{text}'. Smriti is keeping this safe for you. ❤️"
        await send_message(sender, reply)
        print(f"[ROUTE-WORKER] Sent acknowledgment to={sender}", flush=True)
    except Exception as exc:
        print(f"[ROUTE-WORKER] Error in handle_text: {exc}", flush=True)


async def handle_unknown(sender: str, message_type: str) -> None:
    """Process unsupported message type: send guidance help message."""
    print(f"[ROUTE-WORKER] Starting unknown handler for sender={sender}, type='{message_type}'", flush=True)
    try:
        reply = (
            "Welcome to Smriti! 🌸\n\n"
            "I can help you preserve your voice memoirs and restore old photographs.\n\n"
            "• Record and send a voice note to transcribe your memoir.\n"
            "• Send an old photo to restore it using AI.\n\n"
            "Currently, text, audio (voice notes), and images (photos) are supported."
        )
        await send_message(sender, reply)
        print(f"[ROUTE-WORKER] Sent help response to={sender}", flush=True)
    except Exception as exc:
        print(f"[ROUTE-WORKER] Error in handle_unknown: {exc}", flush=True)


@router.get("/webhook", response_class=PlainTextResponse)
async def verify_meta_webhook(request: Request) -> PlainTextResponse:
    """Handle Meta's one-time webhook verification request."""
    query_params = dict(request.query_params)
    print(f"[WEBHOOK] GET /webhook received - all query params: {query_params}", flush=True)

    mode = query_params.get("hub.mode")
    token = query_params.get("hub.verify_token")
    challenge = query_params.get("hub.challenge")

    missing = [name for name in REQUIRED_GET_PARAMS if not query_params.get(name)]
    if missing:
        print(
            f"[WEBHOOK] GET verification failed: missing required params: {missing}; "
            f"received keys: {list(query_params.keys())}",
            flush=True,
        )
        # Raise 422 Unprocessable Entity for missing parameters
        raise HTTPException(
            status_code=422,
            detail=f"Missing required query parameters: {', '.join(missing)}",
        )

    print(
        f"[WEBHOOK] GET verification attempt: mode={mode}, "
        f"token={mask_secret(token)}, challenge={challenge}",
        flush=True,
    )
    try:
        verified_challenge = verify_webhook(mode, token, challenge)
        print("[WEBHOOK] GET verification succeeded", flush=True)
        return PlainTextResponse(content=verified_challenge, status_code=200)
    except Exception as exc:
        print(f"[WEBHOOK] GET verification failed: {exc}", flush=True)
        raise HTTPException(status_code=403, detail="Webhook verification failed") from exc


@router.post("/webhook")
async def receive_meta_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """Receive WhatsApp webhook events from Meta; interview flow via background tasks."""
    body = await request.body()
    print("[WEBHOOK] Received POST /webhook", flush=True)
    print(f"[WEBHOOK] Body length={len(body)} bytes, preview (first 500): {body[:500]}", flush=True)

    try:
        payload: dict[str, Any] = json.loads(body)
        # Direct indexing: status-only callbacks lack "messages" and raise KeyError/IndexError.
        message = payload["entry"][0]["changes"][0]["value"]["messages"][0]
        sender = message["from"]
        message_type = message["type"]

        print(
            f"[WEBHOOK] Parsed message: sender={sender}, type={message_type}",
            flush=True,
        )

        if message_type == "audio":
            media_id = message["audio"]["id"]
            background_tasks.add_task(handle_incoming_voice_answer, sender, media_id)
            print(f"[WEBHOOK] Queued voice answer for sender={sender}", flush=True)
        elif message_type == "text":
            if get_state(sender) is None:
                background_tasks.add_task(start_interview, sender)
                print(f"[WEBHOOK] Queued start_interview for sender={sender}", flush=True)
            else:
                background_tasks.add_task(
                    send_message,
                    sender,
                    "Please reply with a voice note so I can capture your story. 🎙️",
                )
                print(f"[WEBHOOK] Interview in progress; asked for voice note from={sender}", flush=True)
        else:
            background_tasks.add_task(
                send_message,
                sender,
                "Please send a voice note to continue the interview. 🎙️",
            )
            print(
                f"[WEBHOOK] Unsupported type={message_type}; asked for voice note from={sender}",
                flush=True,
            )

    except (KeyError, IndexError) as exc:
        print(f"[WEBHOOK] Ignored non-message payload (status update?): {exc}", flush=True)
        return {"status": "ignored"}
    except Exception as exc:
        print(f"[WEBHOOK] Error processing payload: {exc}", flush=True)

    print("[WEBHOOK] Returning 200 OK immediately (background work queued)", flush=True)
    return {"status": "ok"}

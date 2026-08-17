import asyncio
import os
from typing import Any

import httpx

from secrets_utils import mask_secret


BASE_URL = "https://graph.facebook.com/v19.0/"

SUPPORTED_MEDIA_TYPES = {"image", "audio", "video", "document"}


def _get_env(name: str) -> str:
    """Read a required environment variable and fail with a clear message."""
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _auth_headers() -> dict[str, str]:
    """Build the bearer token headers required by the Meta Graph API."""
    token = _get_env("WHATSAPP_TOKEN")
    return {"Authorization": f"Bearer {token}"}


def _raise_api_error(exc: httpx.HTTPStatusError) -> None:
    """Raise a clear error message for non-2xx Meta API responses."""
    try:
        error_body: Any = exc.response.json()
    except ValueError:
        error_body = exc.response.text

    raise RuntimeError(
        f"Meta API request failed with status {exc.response.status_code}: {error_body}"
    ) from exc


def _ipv4_transport() -> httpx.AsyncHTTPTransport:
    """Force IPv4 — HF Spaces often cannot reach graph.facebook.com over IPv6."""
    return httpx.AsyncHTTPTransport(local_address="0.0.0.0")


async def send_message(to: str, text: str) -> dict:
    """Send a plain text WhatsApp message and return the Meta API response."""
    phone_id = _get_env("WHATSAPP_PHONE_ID")
    url = f"{BASE_URL}{phone_id}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }

    timeout = httpx.Timeout(20.0, connect=20.0)
    last_connect_error: Exception | None = None

    for attempt in (1, 2):
        print(
            f"[META] Sending text message attempt={attempt}/2 to={to}, "
            f"url={url}, phone_id={mask_secret(phone_id)}",
            flush=True,
        )
        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                transport=_ipv4_transport(),
            ) as client:
                response = await client.post(url, headers=_auth_headers(), json=payload)
                print(
                    f"[META] Send response: status={response.status_code}, "
                    f"body={response.text[:500]}",
                    flush=True,
                )
                response.raise_for_status()
                result = response.json()
                message_id = result.get("messages", [{}])[0].get("id", "unknown")
                print(f"[META] Send succeeded: message_id={message_id}", flush=True)
                return result
        except httpx.HTTPStatusError as exc:
            print(
                f"[META] Send failed: status={exc.response.status_code}, "
                f"body={exc.response.text[:500]}",
                flush=True,
            )
            _raise_api_error(exc)
        except (httpx.ConnectTimeout, httpx.ConnectError) as exc:
            last_connect_error = exc
            print(
                f"[META] Connect failed on attempt={attempt}/2 url={url}: {exc}",
                flush=True,
            )
            if attempt == 1:
                await asyncio.sleep(2.0)
                continue
            raise RuntimeError(f"Failed to send WhatsApp message: {exc}") from exc
        except httpx.RequestError as exc:
            print(f"[META] Send request error: {exc}", flush=True)
            raise RuntimeError(f"Failed to send WhatsApp message: {exc}") from exc

    raise RuntimeError(f"Failed to send WhatsApp message: {last_connect_error}")


async def send_media_message(to: str, image_url: str) -> dict:
    """Send an image message by public URL (link type)."""
    phone_id = _get_env("WHATSAPP_PHONE_ID")
    url = f"{BASE_URL}{phone_id}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {"link": image_url},
    }

    print(f"[META] Sending image message to={to}, url={image_url}, phone_id={mask_secret(phone_id)}", flush=True)

    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            transport=_ipv4_transport(),
        ) as client:
            response = await client.post(url, headers=_auth_headers(), json=payload)
            print(
                f"[META] Media send response: status={response.status_code}, "
                f"body={response.text[:500]}",
                flush=True,
            )
            response.raise_for_status()
            result = response.json()
            message_id = result.get("messages", [{}])[0].get("id", "unknown")
            print(f"[META] Media send succeeded: message_id={message_id}", flush=True)
            return result
    except httpx.HTTPStatusError as exc:
        print(
            f"[META] Media send failed: status={exc.response.status_code}, "
            f"body={exc.response.text[:500]}",
            flush=True,
        )
        _raise_api_error(exc)
    except httpx.RequestError as exc:
        print(f"[META] Media send request error: {exc}", flush=True)
        raise RuntimeError(f"Failed to send WhatsApp media message: {exc}") from exc


async def download_media(media_id: str) -> tuple[bytes, str | None]:
    """Download media bytes (audio, image, etc.) from a WhatsApp media ID.

    Returns (content_bytes, mime_type). mime_type may be None if Meta omits it.
    """
    media_url_endpoint = f"{BASE_URL}{media_id}"

    print(f"[META] Downloading media media_id={mask_secret(media_id)}", flush=True)

    try:
        async with httpx.AsyncClient(
            timeout=60.0,
            transport=_ipv4_transport(),
        ) as client:
            media_response = await client.get(
                media_url_endpoint,
                headers=_auth_headers(),
            )
            media_response.raise_for_status()
            media_data = media_response.json()

            download_url = media_data.get("url")
            if not download_url:
                raise RuntimeError("Meta API response did not include a media download URL")

            mime_type = media_data.get("mime_type")

            download_response = await client.get(
                download_url,
                headers=_auth_headers(),
            )
            download_response.raise_for_status()
            print(
                f"[META] Media downloaded: {len(download_response.content)} bytes, "
                f"mime_type={mime_type}",
                flush=True,
            )
            return download_response.content, mime_type
    except httpx.HTTPStatusError as exc:
        print(f"[META] Media download failed: status={exc.response.status_code}", flush=True)
        _raise_api_error(exc)
    except httpx.RequestError as exc:
        print(f"[META] Media download request error: {exc}", flush=True)
        raise RuntimeError(f"Failed to download WhatsApp media: {exc}") from exc


async def download_voice_note(media_id: str) -> bytes:
    """Download raw voice note bytes from a WhatsApp media ID (bytes only)."""
    content, _mime_type = await download_media(media_id)
    return content


def verify_webhook(mode: str, token: str, challenge: str) -> str:
    """Verify Meta webhook setup and return the challenge when the token matches."""
    verify_token = _get_env("WHATSAPP_VERIFY_TOKEN")

    if mode == "subscribe" and token == verify_token:
        return challenge

    raise ValueError(
        "Webhook verification failed: invalid mode or verify token "
        f"(mode={mode!r}, received={mask_secret(token)}, "
        f"expected={mask_secret(verify_token)}, "
        f"len_received={len(token) if token else 0}, "
        f"len_expected={len(verify_token) if verify_token else 0})"
    )


if __name__ == "__main__":
    # Test verify_webhook logic — token must match Meta's Verify Token exactly
    os.environ["WHATSAPP_VERIFY_TOKEN"] = "smriti2026"
    print("Testing verify_webhook with correct token...")
    try:
        res = verify_webhook("subscribe", "smriti2026", "challenge_123")
        print(f"Result: {res} (EXPECTED: challenge_123)")
    except Exception as e:
        print(f"Failed: {e}")

    print("Testing verify_webhook with incorrect token...")
    try:
        verify_webhook("subscribe", "wrong_token", "challenge_123")
        print("Result: Success (UNEXPECTED)")
    except ValueError as e:
        print(f"Result: Failed as expected ({e})")


"""Automated end-to-end test suite for the WhatsApp Adapter.

Usage:
    python test_adapter.py [base_url]
"""

import sys
import asyncio
import httpx

# Default base URL
DEFAULT_BASE_URL = "http://127.0.0.1:7860"

def get_payload(msg_type: str, data_key: str, data_val: dict) -> dict:
    """Helper to generate Meta WhatsApp webhook payload."""
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15551234567",
                                "phone_number_id": "PHONE_NUMBER_ID"
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "Test User"},
                                    "wa_id": "919876543210"
                                }
                            ],
                            "messages": [
                                {
                                    "from": "919876543210",
                                    "id": f"wamid.TEST_ID_{msg_type.upper()}",
                                    "timestamp": "1710000000",
                                    "type": msg_type,
                                    data_key: data_val
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }

async def test_health_check(client: httpx.AsyncClient, base_url: str) -> bool:
    """GET /health -> expect {"status": "ok"}"""
    url = f"{base_url}/health"
    try:
        response = await client.get(url)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("status") == "ok", f"Expected 'status': 'ok', got {data}"
        return True
    except Exception as exc:
        print(f"  [ERROR] {exc}")
        return False

async def test_webhook_get_valid(client: httpx.AsyncClient, base_url: str) -> bool:
    """GET /webhook?hub.mode=subscribe&hub.verify_token=smriti2026&hub.challenge=abc123"""
    url = f"{base_url}/webhook"
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "smriti2026",
        "hub.challenge": "abc123"
    }
    try:
        response = await client.get(url, params=params)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.text == "abc123", f"Expected body 'abc123', got '{response.text}'"
        return True
    except Exception as exc:
        print(f"  [ERROR] {exc}")
        return False

async def test_webhook_get_invalid_token(client: httpx.AsyncClient, base_url: str) -> bool:
    """GET /webhook with invalid verify token -> expect 403"""
    url = f"{base_url}/webhook"
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "wrong_token",
        "hub.challenge": "abc123"
    }
    try:
        response = await client.get(url, params=params)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        return True
    except Exception as exc:
        print(f"  [ERROR] {exc}")
        return False

async def test_webhook_get_missing_params(client: httpx.AsyncClient, base_url: str) -> bool:
    """GET /webhook (no params) -> expect 422 with helpful message"""
    url = f"{base_url}/webhook"
    try:
        response = await client.get(url)
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        # FastAPI validation structure check
        data = response.json()
        assert "detail" in data, f"Expected validation error detail, got {data}"
        return True
    except Exception as exc:
        print(f"  [ERROR] {exc}")
        return False

async def test_webhook_post_text(client: httpx.AsyncClient, base_url: str) -> bool:
    """POST /webhook with text message payload -> expect 200 {"status": "ok"}"""
    url = f"{base_url}/webhook"
    payload = get_payload("text", "text", {"body": "Hello from automated test!"})
    try:
        response = await client.post(url, json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json() == {"status": "ok"}, f"Expected {{'status': 'ok'}}, got {response.json()}"
        return True
    except Exception as exc:
        print(f"  [ERROR] {exc}")
        return False

async def test_webhook_post_voice(client: httpx.AsyncClient, base_url: str) -> bool:
    """POST /webhook with voice note payload -> expect 200 {"status": "ok"}"""
    url = f"{base_url}/webhook"
    payload = get_payload("audio", "audio", {"id": "test_audio_media_id_123", "mime_type": "audio/ogg"})
    try:
        response = await client.post(url, json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json() == {"status": "ok"}, f"Expected {{'status': 'ok'}}, got {response.json()}"
        return True
    except Exception as exc:
        print(f"  [ERROR] {exc}")
        return False

async def test_webhook_post_image(client: httpx.AsyncClient, base_url: str) -> bool:
    """POST /webhook with image payload -> expect 200 {"status": "ok"}"""
    url = f"{base_url}/webhook"
    payload = get_payload("image", "image", {"id": "test_image_media_id_123", "mime_type": "image/jpeg"})
    try:
        response = await client.post(url, json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json() == {"status": "ok"}, f"Expected {{'status': 'ok'}}, got {response.json()}"
        return True
    except Exception as exc:
        print(f"  [ERROR] {exc}")
        return False

async def test_webhook_post_unknown(client: httpx.AsyncClient, base_url: str) -> bool:
    """POST /webhook with unknown type payload -> expect 200 {"status": "ok"}"""
    url = f"{base_url}/webhook"
    # generate a payload with a type 'location'
    payload = get_payload("location", "location", {"latitude": 0.0, "longitude": 0.0})
    try:
        response = await client.post(url, json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json() == {"status": "ok"}, f"Expected {{'status': 'ok'}}, got {response.json()}"
        return True
    except Exception as exc:
        print(f"  [ERROR] {exc}")
        return False

async def run_all_tests(base_url: str):
    print(f"Running automated test suite against: {base_url}\n")
    
    test_cases = [
        ("test_health_check", test_health_check),
        ("test_webhook_get_valid", test_webhook_get_valid),
        ("test_webhook_get_invalid_token", test_webhook_get_invalid_token),
        ("test_webhook_get_missing_params", test_webhook_get_missing_params),
        ("test_webhook_post_text", test_webhook_post_text),
        ("test_webhook_post_voice", test_webhook_post_voice),
        ("test_webhook_post_image", test_webhook_post_image),
        ("test_webhook_post_unknown", test_webhook_post_unknown),
    ]

    passed = 0
    failed = 0
    total = len(test_cases)

    async with httpx.AsyncClient(timeout=10.0) as client:
        for name, test_func in test_cases:
            print(f"Running {name}...")
            success = await test_func(client, base_url)
            if success:
                print(f"PASS: {name}")
                passed += 1
            else:
                print(f"FAIL: {name}")
                failed += 1
            print("-" * 50)

    print("\n" + "=" * 50)
    print(f"TEST SUMMARY:")
    print(f"Total: {total} | Passed: {passed} | Failed: {failed}")
    print("=" * 50)
    
    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BASE_URL
    asyncio.run(run_all_tests(base))

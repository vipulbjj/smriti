"""Optional live-server E2E tests (skipped unless WHISPER_E2E_URL is set)."""

import os

import httpx
import pytest

BASE_URL = os.environ.get("WHISPER_E2E_URL", "").rstrip("/")
FIXTURE = os.path.join(os.path.dirname(__file__), "..", "qa-report", "fixtures", "sample.wav")


pytestmark = pytest.mark.skipif(not BASE_URL, reason="Set WHISPER_E2E_URL=http://127.0.0.1:7860 to run live E2E")


@pytest.fixture
def live_client():
    with httpx.Client(base_url=BASE_URL, timeout=httpx.Timeout(10.0, read=600.0)) as client:
        yield client


def test_live_health(live_client: httpx.Client):
    response = live_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_live_transcribe_empty(live_client: httpx.Client):
    response = live_client.post(
        "/transcribe",
        files={"file": ("empty.wav", b"", "audio/wav")},
    )
    assert response.status_code == 400


def test_live_transcribe_happy_path(live_client: httpx.Client):
    if not os.path.isfile(FIXTURE):
        pytest.skip("sample.wav fixture missing")
    with open(FIXTURE, "rb") as audio:
        response = live_client.post(
            "/transcribe",
            files={"file": ("sample.wav", audio, "audio/wav")},
        )
    assert response.status_code == 200
    data = response.json()
    assert "transcript" in data
    assert "raw_transcript" in data
    assert "language" in data
    assert "corrections_made" in data
    assert isinstance(data["corrections_made"], bool)

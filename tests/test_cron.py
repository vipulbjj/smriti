"""Tests for Vercel cron endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from smriti.config import config
from smriti.db import Family, Grandparent, Story, get_engine, init_db
from sqlmodel import Session


@pytest.fixture(autouse=True)
def use_test_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(config, "database_url", f"sqlite:///{db_path}")
    monkeypatch.setattr(config, "cron_secret", "test-secret-abc")
    import smriti.db as db_module
    db_module._engine = None
    init_db()
    yield
    db_module._engine = None


@pytest.fixture
def client():
    from smriti.main import app
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-secret-abc"}


# --- Auth guard ---

def test_cron_rejects_missing_auth(client):
    resp = client.get("/cron/send-prompts")
    assert resp.status_code == 401


def test_cron_rejects_wrong_secret(client):
    resp = client.get("/cron/send-prompts", headers={"Authorization": "Bearer wrong"})
    assert resp.status_code == 401


# --- send-prompts ---

@patch("smriti.cron.send_daily_prompts", return_value=3)
def test_send_prompts_returns_count(mock_fn, client, auth_headers):
    resp = client.get("/cron/send-prompts", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["sent"] == 3
    mock_fn.assert_called_once()


# --- send-reminders ---

@patch("smriti.cron.send_reminders", return_value=1)
def test_send_reminders_returns_count(mock_fn, client, auth_headers):
    resp = client.get("/cron/send-reminders", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["sent"] == 1


# --- poll-videos ---

@patch("smriti.cron._poll_pending_videos", return_value=2)
def test_poll_videos_returns_count(mock_fn, client, auth_headers):
    resp = client.get("/cron/poll-videos", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["updated"] == 2


# --- process-pending ---

@patch("smriti.cron.process_pending_stories", return_value=4)
def test_process_pending_returns_count(mock_fn, client, auth_headers):
    resp = client.get("/cron/process-pending", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["processed"] == 4


# --- _poll_pending_videos: send before update ---

def test_poll_videos_send_before_update():
    """Video URL must only be written to DB after the WhatsApp send succeeds."""
    call_order = []

    def fake_get_video_url(job_id):
        return "https://cdn.shotstack.io/done.mp4"

    def fake_send_media(phone, caption, url):
        call_order.append("send")

    def fake_update_story_fields(story_id, **fields):
        if "video_url" in fields:
            call_order.append("update")

    # Patch at the module level where _poll_pending_videos imports them
    with (
        patch("smriti.video.get_video_url", fake_get_video_url),
        patch("smriti.whatsapp.send_media_message", fake_send_media),
        patch("smriti.db.update_story_fields", fake_update_story_fields),
    ):
        # Stub out the DB query to return a single pending row
        from smriti.cron import _poll_pending_videos
        from unittest.mock import MagicMock

        fake_story = MagicMock()
        fake_story.id = 1
        fake_story.video_job_id = "job123"
        fake_story.prompt_index = 0
        fake_gp = MagicMock()
        fake_gp.phone = "+912222222222"
        fake_gp.language = "english"
        fake_gp.name = "Nanu"

        with patch("smriti.db.open_session") as mock_session_ctx:
            mock_session = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            mock_session_ctx.return_value = mock_session
            mock_session.exec.return_value.all.return_value = [fake_story]
            mock_session.get.return_value = fake_gp

            _poll_pending_videos()

    assert call_order == ["send", "update"], (
        "send_media_message must be called before update_story_fields so that "
        "a failed send causes the story to be retried on the next poll"
    )

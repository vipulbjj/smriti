"""
Webhook integration tests — no real Twilio or OpenAI calls.
All external services are mocked.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from smriti.config import config
from smriti.db import (
    Family,
    Grandparent,
    Language,
    SubscriptionTier,
    get_engine,
    get_grandparent_by_phone,
    init_db,
    get_family_stories,
)
from sqlmodel import Session


@pytest.fixture(autouse=True)
def use_test_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(config, "database_url", f"sqlite:///{db_path}")
    import smriti.db as db_module
    db_module._engine = None
    init_db()
    yield
    db_module._engine = None


@pytest.fixture
def client():
    # Import app after DB is patched
    from smriti.main import app
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def seeded_grandparent():
    with Session(get_engine(), expire_on_commit=False) as session:
        family = Family(grandchild_name="Vipul", grandchild_phone="+919876543210")
        session.add(family)
        session.commit()
        session.refresh(family)
        gp = Grandparent(
            family_id=family.id,
            name="Nanu",
            phone="+919876543211",
            language=Language.hindi,
        )
        session.add(gp)
        session.commit()
        session.refresh(gp)
        return family, gp


@patch("smriti.webhook.send_message")
def test_text_reply_stored(mock_send, client, seeded_grandparent):
    family, gp = seeded_grandparent
    response = client.post(
        "/webhook/whatsapp",
        data={
            "From": "whatsapp:+919876543211",
            "Body": "मैं अमृतसर के पास एक छोटे से गाँव में पला-बढ़ा।",
            "NumMedia": "0",
        },
    )
    assert response.status_code == 200

    # Story should be saved
    pairs = get_family_stories(family.id)
    _, stories = pairs[0]
    assert len(stories) == 1
    assert "अमृतसर" in stories[0].reply_text

    # Acknowledgement sent
    mock_send.assert_called_once()
    ack_body = mock_send.call_args[0][1]
    assert "शुक्रिया" in ack_body


@patch("smriti.webhook.send_message")
def test_unknown_sender_ignored(mock_send, client):
    response = client.post(
        "/webhook/whatsapp",
        data={
            "From": "whatsapp:+910000000000",
            "Body": "Hello",
            "NumMedia": "0",
        },
    )
    assert response.status_code == 200
    mock_send.assert_not_called()


@patch("smriti.webhook.send_message")
@patch("smriti.webhook.download_voice_note", return_value=b"fake_audio")
@patch("smriti.webhook.transcribe", return_value="यह मेरी आवाज़ है।")
def test_voice_note_transcribed_and_stored(mock_transcribe, mock_download, mock_send, client, seeded_grandparent):
    family, gp = seeded_grandparent
    response = client.post(
        "/webhook/whatsapp",
        data={
            "From": "whatsapp:+919876543211",
            "Body": "",
            "NumMedia": "1",
            "MediaUrl0": "https://api.twilio.com/fake/media/123",
            "MediaContentType0": "audio/ogg",
        },
    )
    assert response.status_code == 200

    mock_download.assert_called_once_with("https://api.twilio.com/fake/media/123")
    mock_transcribe.assert_called_once_with(b"fake_audio", language="hindi")

    pairs = get_family_stories(family.id)
    _, stories = pairs[0]
    assert "आवाज़" in stories[0].reply_text
    assert stories[0].voice_note_url == "https://api.twilio.com/fake/media/123"


@patch("smriti.webhook.send_message")
def test_prompt_index_advances_after_reply(mock_send, client, seeded_grandparent):
    family, gp = seeded_grandparent
    assert gp.prompt_index == 0

    client.post(
        "/webhook/whatsapp",
        data={
            "From": "whatsapp:+919876543211",
            "Body": "First story",
            "NumMedia": "0",
        },
    )

    updated = get_grandparent_by_phone("+919876543211")
    assert updated.prompt_index == 1


@patch("smriti.webhook.send_message")
def test_inactive_grandparent_gets_completion_message(mock_send, client, seeded_grandparent):
    family, gp = seeded_grandparent
    # Mark as inactive (all 52 done)
    with Session(get_engine()) as session:
        gp_db = session.get(Grandparent, gp.id)
        gp_db.active = False
        gp_db.prompt_index = 52
        session.add(gp_db)
        session.commit()

    client.post(
        "/webhook/whatsapp",
        data={
            "From": "whatsapp:+919876543211",
            "Body": "Hello",
            "NumMedia": "0",
        },
    )
    mock_send.assert_called_once()

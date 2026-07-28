"""
Webhook integration tests — no real Twilio or OpenAI calls.
All external services are mocked.
"""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from smriti.config import config
from smriti.db import (
    Family,
    Grandparent,
    Language,
    Story,
    SubscriptionTier,
    get_engine,
    get_grandparent_by_phone,
    init_db,
    get_family_stories,
)
from smriti.photo_story import PhotoStoryResult
from sqlmodel import Session, select


def _photo_seeds():
    """Seeds are excluded from get_family_stories, so fetch them directly."""
    with Session(get_engine()) as session:
        return session.exec(
            select(Story).where(Story.is_photo_seed == True)  # noqa: E712
        ).all()


@pytest.fixture(autouse=True)
def use_test_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(config, "database_url", f"sqlite:///{db_path}")
    monkeypatch.setattr(config, "validate_twilio_signature", False)
    import smriti.db as db_module
    from smriti import ratelimit
    db_module._engine = None
    ratelimit.reset()  # in-memory limiter is module-global — clear between tests
    init_db()
    yield
    db_module._engine = None


@pytest.fixture
def client():
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
            consented_at=datetime.now(timezone.utc),  # already opted in (past onboarding)
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

    pairs = get_family_stories(family.id)
    _, stories = pairs[0]
    assert len(stories) == 1
    assert "अमृतसर" in stories[0].reply_text

    mock_send.assert_called_once()
    ack_body = mock_send.call_args[0][1]
    assert "शुक्रिया" in ack_body
    assert "Nanu" in ack_body


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
            "Body": "मेरी पहली कहानी यहाँ है।",  # >15 chars — passes the length guard
            "NumMedia": "0",
        },
    )

    updated = get_grandparent_by_phone("+919876543211")
    assert updated.prompt_index == 1


@patch("smriti.webhook.send_message")
def test_inactive_grandparent_gets_completion_message(mock_send, client, seeded_grandparent):
    family, gp = seeded_grandparent
    with Session(get_engine()) as session:
        gp_db = session.get(Grandparent, gp.id)
        gp_db.active = False
        gp_db.prompt_index = 7
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
    msg = mock_send.call_args[0][1]
    assert "सात" in msg


@patch("smriti.webhook.send_message")
def test_duplicate_message_sid_ignored(mock_send, client, seeded_grandparent):
    """Twilio retries must not create duplicate stories."""
    family, gp = seeded_grandparent
    payload = {
        "From": "whatsapp:+919876543211",
        "Body": "एक बार की बात है, जब मैं छोटा था।",
        "NumMedia": "0",
        "MessageSid": "SM_TEST_DEDUP_001",
    }

    client.post("/webhook/whatsapp", data=payload)
    client.post("/webhook/whatsapp", data=payload)  # duplicate retry

    pairs = get_family_stories(family.id)
    _, stories = pairs[0]
    assert len(stories) == 1  # only one story despite two requests


@patch("smriti.webhook.send_message")
@patch("smriti.webhook.download_voice_note", side_effect=RuntimeError("network error"))
def test_voice_note_error_sends_error_message(mock_download, mock_send, client, seeded_grandparent):
    """If voice note download fails, send an error message and don't save a story."""
    family, gp = seeded_grandparent
    response = client.post(
        "/webhook/whatsapp",
        data={
            "From": "whatsapp:+919876543211",
            "Body": "",
            "NumMedia": "1",
            "MediaUrl0": "https://api.twilio.com/fake/media/bad",
            "MediaContentType0": "audio/ogg",
        },
    )
    assert response.status_code == 200

    mock_send.assert_called_once()
    error_body = mock_send.call_args[0][1]
    assert "⚠️" in error_body  # error message sent, not ACK

    pairs = get_family_stories(family.id)
    _, stories = pairs[0]
    assert len(stories) == 0  # no story saved


@patch("smriti.webhook.send_message")
def test_completion_notifies_grandchild(mock_send, client, seeded_grandparent):
    """When the seventh story is saved, the grandchild receives a notification."""
    family, gp = seeded_grandparent
    # Put grandparent at prompt 6 (last one)
    with Session(get_engine()) as session:
        gp_db = session.get(Grandparent, gp.id)
        gp_db.prompt_index = 6
        session.add(gp_db)
        session.commit()

    client.post(
        "/webhook/whatsapp",
        data={
            "From": "whatsapp:+919876543211",
            "Body": "यह मेरा आखिरी जवाब है, बहुत अच्छा लगा।",
            "NumMedia": "0",
        },
    )

    # Should have called send_message twice: ACK to grandparent + notification to grandchild
    assert mock_send.call_count == 2
    phones_called = {call[0][0] for call in mock_send.call_args_list}
    assert "+919876543211" in phones_called   # grandparent ACK
    assert "+919876543210" in phones_called   # grandchild notification


@patch("smriti.webhook.send_message")
@patch("smriti.webhook.download_voice_note", return_value=b"fake_photo_bytes")
def test_photo_attachment_stored_permanently(mock_download, mock_send, client, seeded_grandparent):
    """Photo + a real (>=15 char) caption is Branch A: unchanged weekly-story behaviour.
    Photos must be downloaded at receive time and stored as bytes, not as a Twilio URL."""
    family, gp = seeded_grandparent
    caption = "यह मेरी शादी की पुरानी तस्वीर है।"
    response = client.post(
        "/webhook/whatsapp",
        data={
            "From": "whatsapp:+919876543211",
            "Body": caption,
            "NumMedia": "1",
            "MediaUrl0": "https://api.twilio.com/fake/media/photo123",
            "MediaContentType0": "image/jpeg",
            "MessageSid": "SM_PHOTO_TEST_001",
        },
    )
    assert response.status_code == 200

    mock_download.assert_called_once_with("https://api.twilio.com/fake/media/photo123")

    pairs = get_family_stories(family.id)
    _, stories = pairs[0]
    assert len(stories) == 1
    story = stories[0]
    assert story.photo_data == b"fake_photo_bytes"
    assert story.reply_text == caption
    assert story.is_photo_seed is False
    # photo_url must point to our permanent endpoint, not the Twilio URL
    assert "/media/photo/" in story.photo_url
    assert "twilio.com" not in story.photo_url

    # ACK sent and prompt advanced — the ordinary weekly path, not the photo-only branch.
    mock_send.assert_called_once()
    updated = get_grandparent_by_phone("+919876543211")
    assert updated.prompt_index == 1


# --- Photo-only branch (immediate vision pipeline, "Immediate + reuse") ---

@patch("smriti.webhook.send_message")
@patch("smriti.webhook.download_voice_note", return_value=b"fake_photo_bytes")
@patch("smriti.webhook.describe_and_story")
def test_photo_only_saves_seed_and_sends_questions_immediately(
    mock_describe, mock_download, mock_send, client, seeded_grandparent
):
    """A bare photo (no real caption) runs the vision pipeline synchronously, saves an
    is_photo_seed row outside the weekly numbering, and sends the elicitation questions
    right away — without advancing the prompt."""
    family, gp = seeded_grandparent
    mock_describe.return_value = PhotoStoryResult(
        description="A couple before an old car.",
        story_seed="Yaadon ki ek jhalak...",
        questions=["Is this your wedding?", "Who is beside you?"],
    )

    response = client.post(
        "/webhook/whatsapp",
        data={
            "From": "whatsapp:+919876543211",
            "Body": "",
            "NumMedia": "1",
            "MediaUrl0": "https://api.twilio.com/fake/media/photo456",
            "MediaContentType0": "image/jpeg",
            "MessageSid": "SM_PHOTO_ONLY_001",
        },
    )
    assert response.status_code == 200

    # Seed is hidden from the memoir-facing query (timeline + printed book)...
    assert get_family_stories(family.id)[0][1] == []
    # ...but the row exists, described, outside the weekly numbering.
    seeds = _photo_seeds()
    assert len(seeds) == 1
    story = seeds[0]
    assert story.is_photo_seed is True
    assert story.photo_description == "A couple before an old car."
    assert story.photo_story_text == "Yaadon ki ek jhalak..."

    # Prompt index unchanged — advance_prompt was NOT called for a photo-only seed.
    updated = get_grandparent_by_phone("+919876543211")
    assert updated.prompt_index == gp.prompt_index == 0

    # The elicitation questions were sent immediately, not the daily cron.
    mock_send.assert_called_once()
    body = mock_send.call_args[0][1]
    assert "Is this your wedding?" in body or "Who is beside you?" in body


@patch("smriti.webhook.send_message")
@patch("smriti.webhook.download_voice_note", return_value=b"fake_photo_bytes")
@patch("smriti.webhook.describe_and_story", return_value=None)
def test_photo_only_vision_failure_sends_generic_ack(
    mock_describe, mock_download, mock_send, client, seeded_grandparent
):
    """If describe_and_story returns None (Groq down / unparseable), fall back to a
    warm generic acknowledgement, leave photo_description empty for the cron to pick
    up later, and never send the bare '📷' dead-end or 500."""
    family, gp = seeded_grandparent
    response = client.post(
        "/webhook/whatsapp",
        data={
            "From": "whatsapp:+919876543211",
            "Body": "",
            "NumMedia": "1",
            "MediaUrl0": "https://api.twilio.com/fake/media/photo789",
            "MediaContentType0": "image/jpeg",
            "MessageSid": "SM_PHOTO_ONLY_002",
        },
    )
    assert response.status_code == 200

    # Seed is hidden from the memoir-facing query but exists with an empty
    # description, so the daily cron will pick it up later.
    assert get_family_stories(family.id)[0][1] == []
    seeds = _photo_seeds()
    assert len(seeds) == 1
    story = seeds[0]
    assert story.is_photo_seed is True
    assert story.photo_description == ""

    updated = get_grandparent_by_phone("+919876543211")
    assert updated.prompt_index == gp.prompt_index == 0

    mock_send.assert_called_once()
    ack_body = mock_send.call_args[0][1]
    assert "शुक्रिया" in ack_body   # warm generic ACK for the Hindi grandparent
    assert ack_body.strip() != "📷"  # never the bare dead-end


@patch("smriti.webhook.send_message")
@patch("smriti.webhook.describe_and_story")
def test_photo_consent_gate_fires_before_vision(mock_describe, mock_send, client, unconsented_grandparent):
    """Regression: consent/rate-limit gates run before any vision work."""
    family, gp = unconsented_grandparent
    client.post(
        "/webhook/whatsapp",
        data={
            "From": "whatsapp:+918888888888",
            "Body": "",
            "NumMedia": "1",
            "MediaUrl0": "https://api.twilio.com/fake/media/photo999",
            "MediaContentType0": "image/jpeg",
        },
    )
    assert get_family_stories(family.id)[0][1] == []
    mock_describe.assert_not_called()


@patch("smriti.webhook.send_message")
def test_short_message_not_saved(mock_send, client, seeded_grandparent):
    """Greetings and accidental taps under 15 chars should not create a memoir entry."""
    family, gp = seeded_grandparent
    client.post(
        "/webhook/whatsapp",
        data={
            "From": "whatsapp:+919876543211",
            "Body": "ok",
            "NumMedia": "0",
        },
    )
    pairs = get_family_stories(family.id)
    _, stories = pairs[0]
    assert len(stories) == 0
    mock_send.assert_not_called()


@patch("smriti.webhook.send_message")
def test_digest_sent_to_grandchild_after_story(mock_send, client, seeded_grandparent):
    """After saving a story (non-completion), the grandchild receives a weekly digest."""
    family, gp = seeded_grandparent

    with patch("smriti.webhook._do_send_digest") as mock_digest:
        client.post(
            "/webhook/whatsapp",
            data={
                "From": "whatsapp:+919876543211",
                "Body": "मैं अमृतसर के पास एक छोटे से गाँव में पला-बढ़ा था।",
                "NumMedia": "0",
            },
        )
        # Digest is queued as a background task; verify the background function was called
        mock_digest.assert_called_once()
        call_kwargs = mock_digest.call_args[1]
        assert call_kwargs["grandparent_name"] == "Nanu"
        assert call_kwargs["family_id"] == family.id


# --- Consent opt-in flow (P2.1) ---

@pytest.fixture
def unconsented_grandparent():
    with Session(get_engine(), expire_on_commit=False) as session:
        family = Family(grandchild_name="Riya", grandchild_phone="+910000000000")
        session.add(family)
        session.commit()
        session.refresh(family)
        gp = Grandparent(family_id=family.id, name="Dadi", phone="+918888888888",
                         language=Language.english)  # consented_at defaults None
        session.add(gp)
        session.commit()
        session.refresh(gp)
        return family, gp


@patch("smriti.webhook.send_message")
def test_unconsented_reply_is_not_saved(mock_send, client, unconsented_grandparent):
    family, gp = unconsented_grandparent
    client.post("/webhook/whatsapp", data={
        "From": "whatsapp:+918888888888",
        "Body": "I grew up in a small village near Amritsar long ago.",
        "NumMedia": "0",
    })
    # No story saved; a consent request was sent
    assert get_family_stories(family.id)[0][1] == []
    assert any("YES" in c.args[1] for c in mock_send.call_args_list)


@patch("smriti.webhook.send_message")
def test_consent_word_opts_in_and_sends_prompt(mock_send, client, unconsented_grandparent):
    family, gp = unconsented_grandparent
    client.post("/webhook/whatsapp", data={
        "From": "whatsapp:+918888888888", "Body": "YES", "NumMedia": "0",
    })
    refreshed = get_grandparent_by_phone("+918888888888")
    assert refreshed.consented_at is not None
    # thank-you + this week's prompt were sent
    assert mock_send.call_count >= 2


# --- Idempotency guard (P1.3) ---

@patch("smriti.webhook.send_message")
def test_duplicate_weekly_reply_rejected_gracefully(mock_send, client, seeded_grandparent):
    family, gp = seeded_grandparent
    long_a = "मैं अमृतसर के पास एक छोटे से गाँव में पला-बढ़ा था और बहुत यादें हैं।"
    # First reply at week 0 saves and advances the prompt to week 1.
    client.post("/webhook/whatsapp", data={
        "From": "whatsapp:+919876543211", "Body": long_a, "NumMedia": "0",
        "MessageSid": "SM1",
    })
    # Force the grandparent back to week 0 to simulate a late reply to the old thread.
    from smriti.db import open_session as _os
    from smriti.db import Grandparent as _GP
    with _os() as s:
        g = s.get(_GP, gp.id); g.prompt_index = 0; s.add(g); s.commit()
    client.post("/webhook/whatsapp", data={
        "From": "whatsapp:+919876543211", "Body": long_a + " दोबारा अलग बात।", "NumMedia": "0",
        "MessageSid": "SM2",
    })
    # Only one story exists for week 0; a polite duplicate message was sent.
    stories = get_family_stories(family.id)[0][1]
    week0 = [s for s in stories if s.prompt_index == 0]
    assert len(week0) == 1
    assert any("already" in c.args[1].lower() or "मिल" in c.args[1] for c in mock_send.call_args_list)


# --- Rate limit (P3.2) ---

def test_rate_limit_blocks_after_max(monkeypatch):
    from smriti import ratelimit
    ratelimit.reset()
    monkeypatch.setattr(ratelimit, "_MAX", 3)
    assert [ratelimit.allow("+91777") for _ in range(3)] == [True, True, True]
    assert ratelimit.allow("+91777") is False
    # a different phone is unaffected
    assert ratelimit.allow("+91888") is True

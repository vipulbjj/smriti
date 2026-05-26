"""Tests for the story-from-image pipeline (photo_story.py + process_pending_photos)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from smriti.config import config
from smriti.db import Family, Grandparent, Story, init_db, open_session
from smriti import photo_story


PHOTO_BYTES = b"\xff\xd8\xff\xe0fake-jpeg-bytes"


def _fake_groq_returning(payload: dict) -> MagicMock:
    """Build a fake Groq client whose chat completion returns `payload` as JSON."""
    client = MagicMock()
    message = MagicMock()
    message.content = json.dumps(payload)
    choice = MagicMock()
    choice.message = message
    client.chat.completions.create.return_value = MagicMock(choices=[choice])
    return client


# --- describe_and_story: provider gating ---

def test_describe_returns_none_without_groq_key(monkeypatch):
    monkeypatch.setattr(config, "groq_api_key", "")
    assert photo_story.describe_and_story(PHOTO_BYTES, "Nanu") is None


def test_describe_returns_none_for_empty_photo(monkeypatch):
    monkeypatch.setattr(config, "groq_api_key", "gsk_test")
    assert photo_story.describe_and_story(b"", "Nanu") is None


# --- describe_and_story: happy path ---

def test_describe_parses_vision_json(monkeypatch):
    monkeypatch.setattr(config, "groq_api_key", "gsk_test")
    payload = {
        "description": "A young couple stands before a Fiat car, the woman in a cotton sari.",
        "story_seed": "Ek jodaa ek purani gaadi ke saamne khada hai...",
        "questions": ["Is this your wedding car?", "Who is on the left?", "Where was this taken?"],
    }
    with patch.object(photo_story, "_get_groq", return_value=_fake_groq_returning(payload)):
        result = photo_story.describe_and_story(PHOTO_BYTES, "Nanu", language="hindi",
                                                prompt_text="Tell us about your wedding day")

    assert result is not None
    assert "Fiat" in result.description
    assert result.story_seed.startswith("Ek jodaa")
    assert len(result.questions) == 3


def test_describe_returns_none_on_too_short_description(monkeypatch):
    monkeypatch.setattr(config, "groq_api_key", "gsk_test")
    payload = {"description": "x", "story_seed": "seed", "questions": []}
    with patch.object(photo_story, "_get_groq", return_value=_fake_groq_returning(payload)):
        assert photo_story.describe_and_story(PHOTO_BYTES, "Nanu") is None


def test_describe_returns_none_on_unparseable_output(monkeypatch):
    monkeypatch.setattr(config, "groq_api_key", "gsk_test")
    client = MagicMock()
    choice = MagicMock()
    choice.message = MagicMock(content="not json at all")
    client.chat.completions.create.return_value = MagicMock(choices=[choice])
    with patch.object(photo_story, "_get_groq", return_value=client):
        assert photo_story.describe_and_story(PHOTO_BYTES, "Nanu") is None


# --- questions_message formatting ---

def test_questions_message_formats_localized_intro():
    result = photo_story.PhotoStoryResult(
        description="d", story_seed="s",
        questions=["Who is this?", "Where?"],
    )
    msg = result.questions_message("Nanu", "hindi")
    assert "Nanu" in msg
    assert "• Who is this?" in msg
    assert "• Where?" in msg


# --- restoration: provider gating ---

def test_restore_returns_none_without_token(monkeypatch):
    monkeypatch.setattr(config, "replicate_api_token", "")
    assert photo_story.restore_photo(PHOTO_BYTES) is None


def test_colorize_returns_none_without_token(monkeypatch):
    monkeypatch.setattr(config, "replicate_api_token", "")
    assert photo_story.colorize_photo(PHOTO_BYTES) is None


def test_restore_returns_none_for_empty_bytes(monkeypatch):
    monkeypatch.setattr(config, "replicate_api_token", "r8_test")
    assert photo_story.restore_photo(b"") is None


# --- restoration: happy path with mocked Replicate + httpx ---

def test_restore_downloads_result_bytes(monkeypatch):
    monkeypatch.setattr(config, "replicate_api_token", "r8_test")
    fake_client = MagicMock()
    fake_client.run.return_value = "https://replicate.delivery/restored.png"

    fake_resp = MagicMock()
    fake_resp.content = b"restored-image-bytes"
    fake_resp.raise_for_status = MagicMock()

    with (
        patch.object(photo_story, "_get_replicate", return_value=fake_client),
        patch("httpx.get", return_value=fake_resp),
    ):
        out = photo_story.restore_photo(PHOTO_BYTES)

    assert out == b"restored-image-bytes"


def test_reconstruct_degrades_to_none_without_token(monkeypatch):
    monkeypatch.setattr(config, "replicate_api_token", "")
    restored, colorized = photo_story.reconstruct_photo(PHOTO_BYTES)
    assert restored is None and colorized is None


# --- process_pending_photos: end-to-end with a real test DB ---

@pytest.fixture
def test_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(config, "database_url", f"sqlite:///{db_path}")
    import smriti.db as db_module
    db_module._engine = None
    init_db()
    yield
    db_module._engine = None


def _seed_photo_story(test_db) -> int:
    with open_session() as session:
        family = Family(grandchild_name="Riya", grandchild_phone="+910000000000")
        session.add(family)
        session.commit()
        session.refresh(family)
        gp = Grandparent(family_id=family.id, name="Nanu", phone="+919999999999",
                         language="hindi")
        session.add(gp)
        session.commit()
        session.refresh(gp)
        story = Story(grandparent_id=gp.id, prompt_index=0, prompt_text="Your wedding day",
                      reply_text="📷", photo_data=PHOTO_BYTES)
        session.add(story)
        session.commit()
        session.refresh(story)
        return story.id


def test_process_pending_photos_writes_fields_and_sends_questions(test_db, monkeypatch):
    monkeypatch.setattr(config, "groq_api_key", "gsk_test")
    story_id = _seed_photo_story(test_db)

    result = photo_story.PhotoStoryResult(
        description="A couple before an old car.",
        story_seed="Yaadon ki ek jhalak...",
        questions=["Is this your wedding?", "Who is beside you?"],
    )
    sent = []

    from smriti import scheduler
    with (
        patch("smriti.photo_story.describe_and_story", return_value=result),
        patch("smriti.photo_story.reconstruct_photo", return_value=(b"restored", b"color")),
        patch.object(scheduler, "send_message", lambda phone, msg: sent.append((phone, msg))),
    ):
        processed = scheduler.process_pending_photos()

    assert processed == 1

    with open_session() as session:
        story = session.get(Story, story_id)
        assert story.photo_description == "A couple before an old car."
        assert story.photo_story_text == "Yaadon ki ek jhalak..."
        assert story.restored_photo_data == b"restored"
        assert story.colorized_photo_data == b"color"

    # Elicitation questions were sent to the grandparent
    assert len(sent) == 1
    assert sent[0][0] == "+919999999999"
    assert "Is this your wedding?" in sent[0][1]


def test_process_pending_photos_skips_already_processed(test_db, monkeypatch):
    monkeypatch.setattr(config, "groq_api_key", "gsk_test")
    story_id = _seed_photo_story(test_db)
    # Mark it already processed
    from smriti.db import update_story_fields
    update_story_fields(story_id, photo_description="already done")

    from smriti import scheduler
    with patch("smriti.photo_story.describe_and_story") as mock_describe:
        processed = scheduler.process_pending_photos()

    assert processed == 0
    mock_describe.assert_not_called()

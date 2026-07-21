"""Tests for WhatsApp command detection and dispatch."""

import pytest
from unittest.mock import MagicMock, patch, call

from smriti.config import config
from smriti.db import Family, Grandparent, Language, Story, get_engine, init_db
from smriti.commands import detect_command, handle_command
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
def family_and_gp():
    with Session(get_engine(), expire_on_commit=False) as session:
        family = Family(
            grandchild_name="Vipul",
            grandchild_phone="+919876543210",
            timeline_token="testtoken123",
        )
        session.add(family)
        session.commit()
        session.refresh(family)
        gp = Grandparent(
            family_id=family.id,
            name="Nanu",
            phone="+919876543211",
            language="hindi",
            prompt_index=5,
        )
        session.add(gp)
        session.commit()
        session.refresh(gp)
        return family, gp


# --- detect_command ---

@pytest.mark.parametrize("body,expected", [
    ("menu", "menu"),
    ("MENU", "menu"),
    ("मेनू", "menu"),
    ("ਮੇਨੂ", "menu"),
    ("audio", "audio"),
    ("AUDIO", "audio"),
    ("आवाज़", "audio"),
    ("ਆਵਾਜ਼", "audio"),
    ("video", "video"),
    ("वीडियो", "video"),
    ("stories", "stories"),
    ("कहानियाँ", "stories"),
    ("repeat", "repeat"),
    ("दोबारा", "repeat"),
    ("ਦੁਬਾਰਾ", "repeat"),
    ("help", "help"),
    ("मदद", "help"),
    ("ਮਦਦ", "help"),
    ("?", "help"),
])
def test_detect_command_aliases(body, expected):
    assert detect_command(body) == expected


@pytest.mark.parametrize("body", [
    "Hello",
    "मेरे बचपन की कहानी",
    "ok",
    "",
    "   ",
])
def test_detect_command_none_for_non_commands(body):
    assert detect_command(body) is None


# --- handle_command dispatch ---

@patch("smriti.commands.send_message")
def test_menu_command(mock_send, family_and_gp):
    _, gp = family_and_gp
    handle_command("menu", gp)
    mock_send.assert_called_once()
    msg = mock_send.call_args[0][1]
    assert "AUDIO" in msg
    assert "VIDEO" in msg
    assert "STORIES" in msg


@patch("smriti.commands.send_message")
def test_help_command(mock_send, family_and_gp):
    _, gp = family_and_gp
    handle_command("help", gp)
    mock_send.assert_called_once()
    msg = mock_send.call_args[0][1]
    assert "smriti" in msg.lower()


@patch("smriti.commands.send_message")
def test_repeat_command_sends_current_prompt(mock_send, family_and_gp):
    _, gp = family_and_gp
    handle_command("repeat", gp)
    mock_send.assert_called_once()
    # prompt for index 5 should be non-empty
    msg = mock_send.call_args[0][1]
    assert len(msg) > 10


@patch("smriti.commands.send_message")
def test_stories_command_shows_count(mock_send, family_and_gp):
    family, gp = family_and_gp
    # Add 3 stories
    with Session(get_engine()) as session:
        for i in range(3):
            session.add(Story(
                grandparent_id=gp.id,
                prompt_index=i,
                prompt_text=f"Q{i}",
                reply_text=f"A{i} — long enough answer",
            ))
        session.commit()

    handle_command("stories", gp)
    mock_send.assert_called_once()
    msg = mock_send.call_args[0][1]
    assert "3" in msg
    assert "7" in msg


@patch("smriti.commands.send_message")
def test_audio_command_no_stories(mock_send, family_and_gp):
    _, gp = family_and_gp
    handle_command("audio", gp)
    mock_send.assert_called_once()
    # Should send a "no stories yet" message, not crash
    msg = mock_send.call_args[0][1]
    assert len(msg) > 5


@patch("smriti.commands.send_media_message")
def test_audio_command_sends_audio_url(mock_media, family_and_gp):
    _, gp = family_and_gp
    with Session(get_engine()) as session:
        session.add(Story(
            grandparent_id=gp.id,
            prompt_index=4,
            prompt_text="Q",
            reply_text="My long answer to the question here",
        ))
        session.commit()

    handle_command("audio", gp)
    mock_media.assert_called_once()
    url_arg = mock_media.call_args[0][2]
    assert "/media/audio/" in url_arg


@patch("smriti.commands.send_message")
def test_video_command_not_ready(mock_send, family_and_gp):
    _, gp = family_and_gp
    with Session(get_engine()) as session:
        session.add(Story(
            grandparent_id=gp.id,
            prompt_index=4,
            prompt_text="Q",
            reply_text="Answer that is long enough",
            video_url="",
        ))
        session.commit()

    handle_command("video", gp)
    mock_send.assert_called_once()
    msg = mock_send.call_args[0][1]
    assert "⏳" in msg


@patch("smriti.commands.send_media_message")
def test_video_command_sends_video_url(mock_media, family_and_gp):
    _, gp = family_and_gp
    with Session(get_engine()) as session:
        session.add(Story(
            grandparent_id=gp.id,
            prompt_index=4,
            prompt_text="Q",
            reply_text="Answer that is long enough",
            video_url="https://cdn.shotstack.io/story.mp4",
        ))
        session.commit()

    handle_command("video", gp)
    mock_media.assert_called_once()
    url_arg = mock_media.call_args[0][2]
    assert "shotstack" in url_arg

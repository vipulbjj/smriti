import pytest
from smriti.prompts import (
    PROMPTS_ENGLISH,
    PROMPTS_HINDI,
    format_whatsapp_prompt,
    get_prompt,
)
from smriti.db import Language
from smriti.program import SPRINT_LENGTH


def test_prompt_libraries_are_available_for_future_themed_sprints():
    assert len(PROMPTS_HINDI) == 52
    assert len(PROMPTS_ENGLISH) == 52


def test_get_prompt_hindi():
    prompt = get_prompt(0, Language.hindi)
    assert "बचपन" in prompt or "गुज़रा" in prompt


def test_get_prompt_english():
    prompt = get_prompt(0, Language.english)
    assert "grow up" in prompt.lower() or "childhood" in prompt.lower()


def test_get_prompt_bounds():
    with pytest.raises(ValueError):
        get_prompt(-1, Language.english)
    with pytest.raises(ValueError):
        get_prompt(SPRINT_LENGTH, Language.english)


def test_get_prompt_last():
    prompt = get_prompt(SPRINT_LENGTH - 1, Language.english)
    assert isinstance(prompt, str)
    assert len(prompt) > 10


def test_format_whatsapp_prompt_hindi():
    msg = format_whatsapp_prompt(0, Language.hindi, "Nanu")
    assert "smriti" in msg
    assert "Nanu" in msg
    assert "1/7" in msg
    assert "आवाज़" in msg  # footer hint
    assert "_(" not in msg  # WhatsApp italic is _text_ not _(text)_


def test_format_whatsapp_prompt_english():
    msg = format_whatsapp_prompt(0, Language.english, "Grandpa")
    assert "smriti" in msg
    assert "Grandpa" in msg
    assert "Day 1/7" in msg
    assert "voice note" in msg
    assert "_(" not in msg


def test_format_whatsapp_prompt_day_numbering():
    msg = format_whatsapp_prompt(SPRINT_LENGTH - 1, Language.english, "Dadi")
    assert "Day 7/7" in msg

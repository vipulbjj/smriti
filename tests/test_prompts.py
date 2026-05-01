import pytest
from smriti.prompts import (
    PROMPTS_ENGLISH,
    PROMPTS_HINDI,
    format_whatsapp_prompt,
    get_prompt,
)
from smriti.db import Language


def test_prompt_counts():
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
        get_prompt(52, Language.english)


def test_get_prompt_last():
    prompt = get_prompt(51, Language.english)
    assert isinstance(prompt, str)
    assert len(prompt) > 10


def test_format_whatsapp_prompt_hindi():
    msg = format_whatsapp_prompt(0, Language.hindi, "Nanu")
    assert "smriti" in msg
    assert "Nanu" in msg
    assert "1/52" in msg
    assert "आवाज़" in msg  # footer hint


def test_format_whatsapp_prompt_english():
    msg = format_whatsapp_prompt(0, Language.english, "Grandpa")
    assert "smriti" in msg
    assert "Grandpa" in msg
    assert "Week 1/52" in msg
    assert "voice note" in msg


def test_format_whatsapp_prompt_week_numbering():
    # Week 52 should say 52/52
    msg = format_whatsapp_prompt(51, Language.english, "Dadi")
    assert "52/52" in msg

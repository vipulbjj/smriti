"""Tests for transcription provider selection — including the smriti-whisper
HTTP provider and its fallback (the reference vertical integration)."""

from unittest.mock import MagicMock, patch

import pytest

from smriti.config import config
from smriti import transcribe as t


def test_huggingface_provider_calls_service(monkeypatch):
    monkeypatch.setattr(config, "transcription_provider", "huggingface")
    monkeypatch.setattr(config, "whisper_service_url", "https://whisper.hf.space")
    monkeypatch.setattr(config, "whisper_api_key", "secret")

    resp = MagicMock()
    resp.json.return_value = {"text": "मैं लाहौर से आया था "}
    resp.raise_for_status = MagicMock()

    with patch("httpx.post", return_value=resp) as post:
        out = t.transcribe(b"oggbytes", language="hindi")
    assert out == "मैं लाहौर से आया था"
    # posted to the service /transcribe with the shared secret
    assert post.call_args.args[0].endswith("/transcribe")
    assert post.call_args.kwargs["data"]["x_api_key"] == "secret"


def test_huggingface_falls_back_to_groq_on_failure(monkeypatch):
    monkeypatch.setattr(config, "transcription_provider", "huggingface")
    monkeypatch.setattr(config, "whisper_service_url", "https://whisper.hf.space")

    with (
        patch("httpx.post", side_effect=RuntimeError("service down")),
        patch("smriti.ai.transcribe_groq", return_value="fallback text") as groq,
    ):
        out = t.transcribe(b"oggbytes", language="english")
    assert out == "fallback text"
    groq.assert_called_once()


def test_default_provider_uses_groq(monkeypatch):
    monkeypatch.setattr(config, "transcription_provider", "groq")
    with patch("smriti.ai.transcribe_groq", return_value="groq text") as groq:
        out = t.transcribe(b"oggbytes", language="hindi")
    assert out == "groq text"
    groq.assert_called_once()


def test_huggingface_without_url_falls_through_to_groq(monkeypatch):
    # provider set but service URL missing → don't attempt HTTP, use Groq
    monkeypatch.setattr(config, "transcription_provider", "huggingface")
    monkeypatch.setattr(config, "whisper_service_url", "")
    with (
        patch("httpx.post") as post,
        patch("smriti.ai.transcribe_groq", return_value="groq text"),
    ):
        out = t.transcribe(b"oggbytes", language="hindi")
    assert out == "groq text"
    post.assert_not_called()

"""API tests with the Whisper pipeline mocked (no model download)."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import app


@pytest.fixture
def mock_asr():
    return MagicMock(
        return_value={"text": "hello world", "language": "english"},
    )


@pytest.fixture
def client(mock_asr):
    with patch("app.pipeline", return_value=mock_asr):
        with TestClient(app.app) as test_client:
            yield test_client


def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_transcribe_returns_transcript(client: TestClient, mock_asr: MagicMock):
    response = client.post(
        "/transcribe",
        files={"file": ("sample.wav", b"fake-audio-bytes", "audio/wav")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["transcript"] == "hello world"
    assert data["raw_transcript"] == "hello world"
    assert data["language"] == "en"
    assert data["corrections_made"] is False
    mock_asr.assert_called_once()
    _, kwargs = mock_asr.call_args
    assert kwargs["generate_kwargs"]["temperature"] == 0.0
    assert kwargs["generate_kwargs"]["compression_ratio_threshold"] == 2.4
    assert "condition_on_previous_text" not in kwargs["generate_kwargs"]


def test_transcribe_groq_cleanup(client: TestClient, mock_asr: MagicMock):
    with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}, clear=False):
        mock_groq_client = MagicMock()
        mock_groq_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="cleaned hello"))]
        )
        with patch("groq.Groq", return_value=mock_groq_client):
            response = client.post(
                "/transcribe",
                files={"file": ("sample.wav", b"fake-audio-bytes", "audio/wav")},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["transcript"] == "cleaned hello"
    assert data["raw_transcript"] == "hello world"
    assert data["corrections_made"] is True


def test_transcribe_model_not_loaded():
    with patch("app.pipeline", return_value=MagicMock()):
        with TestClient(app.app) as client:
            app.asr_pipeline = None
            response = client.post(
                "/transcribe",
                files={"file": ("sample.wav", b"audio", "audio/wav")},
            )

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "error": "model_unavailable",
        "message": "Whisper model is not loaded",
    }


def test_transcribe_empty_file(client: TestClient):
    response = client.post(
        "/transcribe",
        files={"file": ("empty.wav", b"", "audio/wav")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "error": "empty_file",
        "message": "Uploaded audio file is empty",
    }


def test_transcribe_pipeline_error_returns_json(client: TestClient, mock_asr: MagicMock):
    mock_asr.side_effect = RuntimeError("decode failed")
    response = client.post(
        "/transcribe",
        files={"file": ("sample.wav", b"fake-audio-bytes", "audio/wav")},
    )

    assert response.status_code == 500
    assert response.json() == {
        "error": "transcription_failed",
        "message": "decode failed",
    }


def test_whisper_generate_kwargs_supported_only():
    assert "condition_on_previous_text" not in app.WHISPER_GENERATE_KWARGS
    assert app.WHISPER_GENERATE_KWARGS.keys() == {
        "compression_ratio_threshold",
        "logprob_threshold",
        "no_speech_threshold",
    }


def test_build_whisper_generate_kwargs_short_audio(tmp_path):
    wav = tmp_path / "short.wav"
    wav.write_bytes(b"placeholder")
    with patch("app.audio_duration_seconds", return_value=1.0):
        kwargs = app.build_whisper_generate_kwargs(str(wav))
    assert kwargs["temperature"] == 0.0


def test_build_whisper_generate_kwargs_long_audio(tmp_path):
    wav = tmp_path / "long.wav"
    wav.write_bytes(b"placeholder")
    with patch("app.audio_duration_seconds", return_value=45.0):
        kwargs = app.build_whisper_generate_kwargs(str(wav))
    assert kwargs["temperature"] == app.WHISPER_LONG_FORM_TEMPERATURES

"""Start uvicorn with mocked Whisper pipeline for QA (no model download)."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import uvicorn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

mock_asr = MagicMock(
    return_value={
        "text": "नमस्ते दुनिया",
        "language": "hindi",
    }
)

with patch("app.pipeline", return_value=mock_asr):
    from app import app as fastapi_app

    uvicorn.run(fastapi_app, host="127.0.0.1", port=7860, log_level="warning")

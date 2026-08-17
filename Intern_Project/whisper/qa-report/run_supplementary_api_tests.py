"""Supplementary API contract tests via TestClient (mocked pipeline)."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import app

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "qa-report" / "supplementary-results.json"


def main() -> int:
    mock = MagicMock(return_value={"text": "hello world", "language": "english"})
    results = []

    with patch("app.pipeline", return_value=mock):
        with TestClient(app.app) as client:
            cases = [
                ("SUP-001", "GET / health", lambda: client.get("/"), 200, {"status": "ok"}),
                (
                    "SUP-002",
                    "POST /transcribe happy",
                    lambda: client.post(
                        "/transcribe",
                        files={"file": ("a.wav", b"bytes", "audio/wav")},
                    ),
                    200,
                    {"transcript": "hello world", "language": "english"},
                ),
                (
                    "SUP-003",
                    "POST empty file",
                    lambda: client.post(
                        "/transcribe",
                        files={"file": ("e.wav", b"", "audio/wav")},
                    ),
                    400,
                    None,
                ),
                ("SUP-004", "POST missing file", lambda: client.post("/transcribe"), 422, None),
                (
                    "SUP-005",
                    "POST path traversal name",
                    lambda: client.post(
                        "/transcribe",
                        files={"file": ("../../x.wav", b"x", "audio/wav")},
                    ),
                    200,
                    None,
                ),
            ]
            for cid, name, fn, exp_status, exp_body in cases:
                r = fn()
                ok = r.status_code == exp_status
                if exp_body is not None:
                    ok = ok and r.json() == exp_body
                results.append(
                    {
                        "id": cid,
                        "name": name,
                        "status": "PASS" if ok else "FAIL",
                        "http_status": r.status_code,
                        "body": r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text,
                    }
                )

            app.asr_pipeline = None
            r = client.post(
                "/transcribe",
                files={"file": ("a.wav", b"x", "audio/wav")},
            )
            results.append(
                {
                    "id": "SUP-006",
                    "name": "503 model not loaded",
                    "status": "PASS" if r.status_code == 503 else "FAIL",
                    "http_status": r.status_code,
                    "body": r.json(),
                }
            )

    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({"path": str(OUT), "passed": sum(1 for x in results if x["status"] == "PASS")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

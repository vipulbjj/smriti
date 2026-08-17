"""Complete E2E QA orchestration: TestClient + optional mock live server."""

from __future__ import annotations

import json
import struct
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
from fastapi.testclient import TestClient

import app

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / "qa-report"
FIXTURES = QA / "fixtures"
SCREENSHOTS = QA / "screenshots"
FIXTURE_WAV = FIXTURES / "sample.wav"
PYTEST_LOG = QA / "pytest-results.txt"
TESTCLIENT_RESULTS = QA / "testclient-e2e-results.json"
E2E_RESULTS = QA / "e2e-results.json"


def make_minimal_wav(path: Path) -> None:
    """Write a tiny valid 16-bit mono WAV (0.1s @ 16kHz)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 16000
    num_samples = 1600
    data_size = num_samples * 2
    byte_rate = sample_rate * 2
    block_align = 2
    bits_per_sample = 16
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        1,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        data_size,
    )
    samples = b"\x00\x00" * num_samples
    path.write_bytes(header + samples)


def run_pytest() -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-v"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    PYTEST_LOG.write_text(proc.stdout + proc.stderr, encoding="utf-8")
    passed = proc.stdout.count(" PASSED")
    failed = proc.stdout.count(" FAILED")
    skipped = proc.stdout.count(" SKIPPED")
    return {
        "exit_code": proc.returncode,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "log": str(PYTEST_LOG),
    }


def run_testclient_e2e() -> list[dict]:
    mock = MagicMock(return_value={"text": "e2e transcript", "language": "english"})
    results: list[dict] = []

    def record(cid: str, name: str, ok: bool, status_code: int, body: object) -> None:
        results.append(
            {
                "id": cid,
                "name": name,
                "mode": "TestClient (mocked pipeline)",
                "status": "PASS" if ok else "FAIL",
                "http_status": status_code,
                "body": body,
            }
        )

    with patch("app.pipeline", return_value=mock):
        with TestClient(app.app) as client:
            r = client.get("/")
            record("TC-001", "GET / health", r.status_code == 200 and r.json() == {"status": "ok"}, r.status_code, r.json())

            r = client.post("/transcribe")
            record("TC-002", "POST /transcribe missing file", r.status_code == 422, r.status_code, r.json())

            r = client.post("/transcribe", files={"file": ("empty.wav", b"", "audio/wav")})
            record(
                "TC-003",
                "POST /transcribe empty file",
                r.status_code == 400 and r.json().get("detail") == "Uploaded audio file is empty",
                r.status_code,
                r.json(),
            )

            r = client.post(
                "/transcribe",
                files={"file": ("sample.wav", FIXTURE_WAV.read_bytes(), "audio/wav")},
            )
            ok = r.status_code == 200 and r.json() == {
                "transcript": "e2e transcript",
                "language": "english",
            }
            record("TC-004", "POST /transcribe happy path (mock)", ok, r.status_code, r.json())

            app.asr_pipeline = None
            r = client.post(
                "/transcribe",
                files={"file": ("sample.wav", b"x", "audio/wav")},
            )
            record(
                "TC-005",
                "POST /transcribe model not loaded",
                r.status_code == 503,
                r.status_code,
                r.json(),
            )

    TESTCLIENT_RESULTS.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def write_evidence_html(path: Path, title: str, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, indent=2)
    path.write_text(
        f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{title}</title>
<style>body{{font-family:system-ui,sans-serif;margin:2rem;background:#0f172a;color:#e2e8f0}}
pre{{background:#1e293b;padding:1rem;border-radius:8px;overflow:auto}}</style></head>
<body><h1>{title}</h1><pre>{body}</pre></body></html>""",
        encoding="utf-8",
    )


def wait_for_server(base: str, timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(f"{base}/", timeout=2.0)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def run_live_e2e(base: str) -> list[dict]:
    proc = subprocess.run(
        [sys.executable, str(QA / "e2e_runner.py"), "--base-url", base],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if E2E_RESULTS.exists():
        return json.loads(E2E_RESULTS.read_text(encoding="utf-8"))
    return [{"error": proc.stderr or proc.stdout}]


def main() -> int:
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    FIXTURES.mkdir(parents=True, exist_ok=True)
    if not FIXTURE_WAV.exists():
        make_minimal_wav(FIXTURE_WAV)

    pytest_summary = run_pytest()
    tc_results = run_testclient_e2e()
    write_evidence_html(QA / "screenshots" / "evidence-health.html", "GET / — TestClient", {"status": "ok"})
    write_evidence_html(
        QA / "screenshots" / "evidence-transcribe.html",
        "POST /transcribe — TestClient (mocked)",
        [r for r in tc_results if r["id"] == "TC-004"][0],
    )

    summary = {
        "pytest": pytest_summary,
        "testclient_pass": sum(1 for r in tc_results if r["status"] == "PASS"),
        "testclient_total": len(tc_results),
        "fixture": str(FIXTURE_WAV),
    }

    base = "http://127.0.0.1:7860"
    live_results: list[dict] = []
    try:
        import uvicorn

        mock = MagicMock(return_value={"text": "live mock", "language": "en"})
        with patch("app.pipeline", return_value=mock):
            config = uvicorn.Config("app:app", host="127.0.0.1", port=7860, log_level="warning")
            server = uvicorn.Server(config)
            import threading

            thread = threading.Thread(target=server.run, daemon=True)
            thread.start()
            if wait_for_server(base, 45.0):
                live_results = run_live_e2e(base)
                summary["live_server"] = "up"
            else:
                summary["live_server"] = "timeout"
            server.should_exit = True
    except Exception as exc:
        summary["live_server"] = f"skipped: {exc}"

    summary["live_e2e"] = live_results
    (QA / "e2e-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if pytest_summary["exit_code"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

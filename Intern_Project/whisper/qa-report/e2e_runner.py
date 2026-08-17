"""Live-server E2E runner. Usage: python qa-report/e2e_runner.py [--base-url URL]"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_WAV = ROOT / "qa-report" / "fixtures" / "sample.wav"
RESULTS_PATH = ROOT / "qa-report" / "e2e-results.json"


def record(results: list[dict], case_id: str, name: str, **fields) -> None:
    results.append({"id": case_id, "name": name, **fields})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:7860")
    parser.add_argument("--transcribe-timeout", type=float, default=600.0)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    results: list[dict] = []

    with httpx.Client(base_url=base, timeout=httpx.Timeout(10.0, read=args.transcribe_timeout)) as client:
        # E2E-001 Health
        t0 = time.perf_counter()
        try:
            r = client.get("/")
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)
            ok = r.status_code == 200 and r.json() == {"status": "ok"}
            record(
                results,
                "E2E-001",
                "Health GET /",
                status="PASS" if ok else "FAIL",
                http_status=r.status_code,
                body=r.text,
                latency_ms=latency_ms,
            )
        except Exception as exc:
            record(results, "E2E-001", "Health GET /", status="FAIL", error=str(exc))

        # E2E-002 Missing file
        try:
            r = client.post("/transcribe")
            record(
                results,
                "E2E-002",
                "Transcribe missing file",
                status="PASS" if r.status_code == 422 else "FAIL",
                http_status=r.status_code,
                body=r.text[:500],
            )
        except Exception as exc:
            record(results, "E2E-002", "Transcribe missing file", status="FAIL", error=str(exc))

        # E2E-003 Empty file
        try:
            r = client.post(
                "/transcribe",
                files={"file": ("empty.wav", b"", "audio/wav")},
            )
            record(
                results,
                "E2E-003",
                "Transcribe empty file",
                status="PASS" if r.status_code == 400 else "FAIL",
                http_status=r.status_code,
                body=r.text[:500],
            )
        except Exception as exc:
            record(results, "E2E-003", "Transcribe empty file", status="FAIL", error=str(exc))

        # E2E-004 Wrong content-type (still multipart)
        try:
            r = client.post(
                "/transcribe",
                files={"file": ("notes.txt", b"not audio", "text/plain")},
            )
            # App does not validate MIME; may 200/500/503 depending on model
            record(
                results,
                "E2E-004",
                "Transcribe text/plain upload",
                status="INFO",
                http_status=r.status_code,
                body=r.text[:500],
            )
        except Exception as exc:
            record(results, "E2E-004", "Transcribe text/plain upload", status="FAIL", error=str(exc))

        # E2E-005 Path traversal filename
        try:
            r = client.post(
                "/transcribe",
                files={"file": ("../../../evil.wav", b"x", "audio/wav")},
            )
            record(
                results,
                "E2E-005",
                "Path traversal filename",
                status="PASS" if r.status_code in (400, 500, 503) else "INFO",
                http_status=r.status_code,
                body=r.text[:500],
            )
        except Exception as exc:
            record(results, "E2E-005", "Path traversal filename", status="FAIL", error=str(exc))

        # E2E-006 Oversized file (50MB) — no server limit documented
        try:
            big = b"\x00" * (50 * 1024 * 1024)
            r = client.post(
                "/transcribe",
                files={"file": ("big.wav", big, "audio/wav")},
                timeout=httpx.Timeout(60.0, read=300.0),
            )
            record(
                results,
                "E2E-006",
                "Oversized 50MB upload",
                status="INFO",
                http_status=r.status_code,
                body=r.text[:200],
            )
        except Exception as exc:
            record(results, "E2E-006", "Oversized 50MB upload", status="INFO", error=str(exc))

        # E2E-007 Happy path (if fixture exists)
        if FIXTURE_WAV.exists():
            try:
                t0 = time.perf_counter()
                with FIXTURE_WAV.open("rb") as fh:
                    r = client.post(
                        "/transcribe",
                        files={"file": ("sample.wav", fh, "audio/wav")},
                        timeout=httpx.Timeout(30.0, read=args.transcribe_timeout),
                    )
                latency_ms = round((time.perf_counter() - t0) * 1000, 1)
                body = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
                ok = (
                    r.status_code == 200
                    and isinstance(body, dict)
                    and "transcript" in body
                    and "language" in body
                )
                record(
                    results,
                    "E2E-007",
                    "Transcribe valid WAV",
                    status="PASS" if ok else ("BLOCKED" if r.status_code == 503 else "FAIL"),
                    http_status=r.status_code,
                    body=body,
                    latency_ms=latency_ms,
                )
            except Exception as exc:
                record(results, "E2E-007", "Transcribe valid WAV", status="FAIL", error=str(exc))

        # E2E-008 CORS preflight
        try:
            r = client.options(
                "/",
                headers={
                    "Origin": "http://evil.example",
                    "Access-Control-Request-Method": "POST",
                },
            )
            cors = {k: v for k, v in r.headers.items() if k.lower().startswith("access-control")}
            record(
                results,
                "E2E-008",
                "CORS preflight",
                status="INFO",
                http_status=r.status_code,
                cors_headers=cors,
            )
        except Exception as exc:
            record(results, "E2E-008", "CORS preflight", status="INFO", error=str(exc))

    RESULTS_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    passed = sum(1 for r in results if r.get("status") == "PASS")
    failed = sum(1 for r in results if r.get("status") == "FAIL")
    print(json.dumps({"passed": passed, "failed": failed, "results_path": str(RESULTS_PATH)}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

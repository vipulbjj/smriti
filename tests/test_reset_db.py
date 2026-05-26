"""Tests for the reset_db guard logic — never the destructive path itself."""

import importlib.util
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "reset_db", Path(__file__).resolve().parent.parent / "scripts" / "reset_db.py"
)
reset_db = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(reset_db)


def test_redact_hides_password():
    url = "postgresql://user:supersecret@db.host:5432/smriti"
    out = reset_db.redact(url)
    assert "supersecret" not in out
    assert "***" in out
    assert "db.host:5432/smriti" in out


def test_refuses_without_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert reset_db.main(["--yes"]) == 2


def test_refuses_without_yes_flag(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h/db")
    # No --yes → must refuse (return 1) and never import/drop anything.
    assert reset_db.main([]) == 1

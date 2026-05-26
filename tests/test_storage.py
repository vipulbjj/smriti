"""Tests for PDF object storage (P1.2) — local fallback and S3/R2 upload path."""

import sys
import types
from unittest.mock import MagicMock

import pytest

from smriti import storage


def test_local_fallback_when_unconfigured(tmp_path, monkeypatch):
    monkeypatch.delenv("STORAGE_BUCKET", raising=False)
    pdf = tmp_path / "book.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    # No bucket → returns the local path unchanged
    assert storage.store_pdf(str(pdf)) == str(pdf)


def test_store_pdf_uploads_and_returns_signed_url(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BUCKET", "smriti-books")
    pdf = tmp_path / "book.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    fake_client = MagicMock()
    fake_client.generate_presigned_url.return_value = "https://cdn/signed/book.pdf?sig=abc"
    monkeypatch.setattr(storage, "_client", lambda: fake_client)

    url = storage.store_pdf(str(pdf))
    assert url == "https://cdn/signed/book.pdf?sig=abc"
    fake_client.upload_fileobj.assert_called_once()
    # key defaults under books/
    args, kwargs = fake_client.generate_presigned_url.call_args
    assert kwargs["Params"]["Key"] == "books/book.pdf"


def test_store_pdf_falls_back_on_upload_error(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BUCKET", "smriti-books")
    pdf = tmp_path / "book.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")

    boom = MagicMock()
    boom.upload_fileobj.side_effect = RuntimeError("network")
    monkeypatch.setattr(storage, "_client", lambda: boom)

    # Upload fails → never lose the file; return the local path.
    assert storage.store_pdf(str(pdf)) == str(pdf)

"""Tests for admin endpoints — timeline token rotation (P2.2)."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from smriti.config import config
from smriti.db import Family, get_engine, get_family_by_token, init_db


@pytest.fixture(autouse=True)
def use_test_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(config, "database_url", f"sqlite:///{db_path}")
    monkeypatch.setattr(config, "admin_key", "admin-secret")
    import smriti.db as db_module
    db_module._engine = None
    init_db()
    yield
    db_module._engine = None


@pytest.fixture
def client():
    from smriti.main import app
    return TestClient(app)


@pytest.fixture
def family():
    with Session(get_engine(), expire_on_commit=False) as session:
        fam = Family(grandchild_name="Riya", grandchild_phone="+910000000000")
        session.add(fam)
        session.commit()
        session.refresh(fam)
        return fam


def test_rotate_token_requires_auth(client, family):
    resp = client.post(f"/admin/api/rotate-token/{family.id}")
    assert resp.status_code == 401


def test_rotate_token_changes_and_invalidates_old(client, family):
    old_token = family.timeline_token
    assert get_family_by_token(old_token) is not None

    resp = client.post(f"/admin/api/rotate-token/{family.id}?key=admin-secret")
    assert resp.status_code == 200
    new_token = resp.json()["new_token"]

    assert new_token != old_token
    assert get_family_by_token(new_token) is not None      # new link works
    assert get_family_by_token(old_token) is None          # old link is dead


def test_rotate_token_unknown_family_404(client):
    resp = client.post("/admin/api/rotate-token/9999?key=admin-secret")
    assert resp.status_code == 404

import pytest
from sqlmodel import Session

from smriti.db import (
    Family,
    Grandparent,
    Language,
    Story,
    SubscriptionTier,
    advance_prompt,
    get_family_stories,
    get_grandparent_by_phone,
    init_db,
    get_engine,
    save_story,
)
from smriti.config import config


@pytest.fixture(autouse=True)
def use_test_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(config, "database_url", f"sqlite:///{db_path}")
    # Reset engine so it picks up the new URL
    import smriti.db as db_module
    db_module._engine = None
    init_db()
    yield
    db_module._engine = None


def _seed_family():
    with Session(get_engine(), expire_on_commit=False) as session:
        family = Family(grandchild_name="Vipul", grandchild_phone="+919876543210")
        session.add(family)
        session.commit()
        session.refresh(family)

        gp = Grandparent(
            family_id=family.id,
            name="Nanu",
            phone="+919876543211",
            language=Language.hindi,
        )
        session.add(gp)
        session.commit()
        session.refresh(gp)
        return family, gp


def test_get_grandparent_by_phone_found():
    family, gp = _seed_family()
    result = get_grandparent_by_phone("+919876543211")
    assert result is not None
    assert result.name == "Nanu"


def test_get_grandparent_by_phone_not_found():
    result = get_grandparent_by_phone("+910000000000")
    assert result is None


def test_save_and_retrieve_story():
    family, gp = _seed_family()
    story = Story(
        grandparent_id=gp.id,
        prompt_index=0,
        prompt_text="Where did you grow up?",
        reply_text="I grew up in a small village near Amritsar.",
    )
    saved = save_story(story)
    assert saved.id is not None

    pairs = get_family_stories(family.id)
    assert len(pairs) == 1
    gp_out, stories = pairs[0]
    assert gp_out.name == "Nanu"
    assert len(stories) == 1
    assert "Amritsar" in stories[0].reply_text


def test_advance_prompt():
    family, gp = _seed_family()
    assert gp.prompt_index == 0
    advance_prompt(gp.id)
    updated = get_grandparent_by_phone("+919876543211")
    assert updated.prompt_index == 1
    assert updated.active is True


def test_advance_prompt_deactivates_at_52():
    family, gp = _seed_family()
    # Manually set to prompt 51
    with Session(get_engine()) as session:
        gp_db = session.get(Grandparent, gp.id)
        gp_db.prompt_index = 51
        session.add(gp_db)
        session.commit()

    advance_prompt(gp.id)
    updated = get_grandparent_by_phone("+919876543211")
    assert updated.prompt_index == 52
    assert updated.active is False

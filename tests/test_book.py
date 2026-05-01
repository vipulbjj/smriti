import os
import pytest
from sqlmodel import Session

from smriti.config import config
from smriti.db import (
    Family,
    Grandparent,
    Language,
    Story,
    get_engine,
    init_db,
)
from smriti.book import generate_book


@pytest.fixture(autouse=True)
def use_test_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(config, "database_url", f"sqlite:///{db_path}")
    import smriti.db as db_module
    db_module._engine = None
    init_db()
    yield
    db_module._engine = None


def _seed(session: Session):
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

    for i in range(5):
        session.add(Story(
            grandparent_id=gp.id,
            prompt_index=i,
            prompt_text=f"Question {i + 1}",
            reply_text=f"This is the answer to question {i + 1}. " * 10,
        ))
    session.commit()
    return family, gp


def test_generate_book_creates_pdf(tmp_path):
    with Session(get_engine(), expire_on_commit=False) as session:
        family, _ = _seed(session)

    output = str(tmp_path / "test_book.pdf")
    path = generate_book(family.id, output_path=output)

    assert path == output
    assert os.path.exists(output)
    assert os.path.getsize(output) > 5000  # Non-trivial PDF


def test_generate_book_unknown_family():
    with pytest.raises(ValueError, match="not found"):
        generate_book(999)


def test_generate_book_no_stories(tmp_path):
    with Session(get_engine()) as session:
        family = Family(grandchild_name="Empty", grandchild_phone="+910000000001")
        session.add(family)
        session.commit()
        session.refresh(family)
        # No grandparents added

    with pytest.raises(ValueError, match="No grandparents"):
        generate_book(family.id)

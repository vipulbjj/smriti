from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine, select

from .config import config


class Language(str, Enum):
    hindi = "hindi"
    english = "english"
    punjabi = "punjabi"


class SubscriptionTier(str, Enum):
    whatsapp = "whatsapp"      # ₹15,000/yr
    concierge = "concierge"    # ₹25,000 one-time
    ai_vault = "ai_vault"      # ₹50,000–₹1,50,000


class Family(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    grandchild_name: str
    grandchild_phone: str          # WhatsApp number, e.g. +919876543210
    grandchild_email: str = ""
    tier: SubscriptionTier = SubscriptionTier.whatsapp
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: str = ""


class Grandparent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    family_id: int = Field(foreign_key="family.id")
    name: str
    phone: str                     # WhatsApp number they reply from
    language: Language = Language.hindi
    # Which prompt index they're on (0-indexed, 0–51)
    prompt_index: int = 0
    # Whether they're actively receiving prompts
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Story(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    grandparent_id: int = Field(foreign_key="grandparent.id")
    prompt_index: int
    prompt_text: str
    reply_text: str = ""
    voice_note_url: str = ""
    twilio_message_sid: str = Field(default="", index=True)
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            config.database_url,
            echo=False,
            connect_args={"check_same_thread": False},
        )
    return _engine


def open_session() -> Session:
    return Session(get_engine(), expire_on_commit=False)


def init_db():
    SQLModel.metadata.create_all(get_engine())


def get_session():
    with open_session() as session:
        yield session


def get_grandparent_by_phone(phone: str) -> Optional[Grandparent]:
    with open_session() as session:
        return session.exec(
            select(Grandparent).where(Grandparent.phone == phone)
        ).first()


def save_story(story: Story) -> Story:
    with open_session() as session:
        session.add(story)
        session.commit()
        session.refresh(story)
        return story


def advance_prompt(grandparent_id: int) -> None:
    with open_session() as session:
        gp = session.get(Grandparent, grandparent_id)
        if gp:
            gp.prompt_index += 1
            if gp.prompt_index >= 52:
                gp.active = False
            session.add(gp)
            session.commit()


def story_exists_by_sid(message_sid: str) -> bool:
    if not message_sid:
        return False
    with open_session() as session:
        return session.exec(
            select(Story).where(Story.twilio_message_sid == message_sid)
        ).first() is not None


def get_family_stories(family_id: int) -> list[tuple[Grandparent, list[Story]]]:
    """Returns [(grandparent, [stories...])] for a family."""
    with open_session() as session:
        grandparents = session.exec(
            select(Grandparent).where(Grandparent.family_id == family_id)
        ).all()
        result = []
        for gp in grandparents:
            stories = session.exec(
                select(Story)
                .where(Story.grandparent_id == gp.id)
                .order_by(Story.prompt_index)
            ).all()
            result.append((gp, list(stories)))
        return result

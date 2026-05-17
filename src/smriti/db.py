import secrets
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
    grandchild_phone: str
    grandchild_email: str = ""
    tier: SubscriptionTier = SubscriptionTier.whatsapp
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: str = ""
    # Shareable token for the family memory timeline
    timeline_token: str = Field(default_factory=lambda: secrets.token_urlsafe(16))


class Grandparent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    family_id: int = Field(foreign_key="family.id")
    name: str
    phone: str
    language: Language = Language.hindi
    prompt_index: int = 0
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Set each time a weekly prompt is sent — used for 3-day reminder logic
    last_prompted_at: Optional[datetime] = Field(default=None)


class Story(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    grandparent_id: int = Field(foreign_key="grandparent.id")
    prompt_index: int
    prompt_text: str
    reply_text: str = ""
    enhanced_text: str = ""        # AI-polished prose version of reply_text
    voice_note_url: str = ""
    photo_url: str = ""            # Serves /media/photo/{story_id} after download
    photo_data: Optional[bytes] = Field(default=None)   # Raw photo bytes (permanent)
    audio_url: str = ""            # Serves /media/audio/{story_id}
    audio_data: Optional[bytes] = Field(default=None)   # Cached TTS bytes
    video_job_id: str = ""         # Shotstack render job ID
    video_url: str = ""            # Final video URL when render completes
    twilio_message_sid: str = Field(default="", index=True)
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


_engine = None


def get_engine():
    global _engine
    if _engine is None:
        connect_args = (
            {"check_same_thread": False}
            if config.database_url.startswith("sqlite")
            else {}
        )
        _engine = create_engine(config.database_url, echo=False, connect_args=connect_args)
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
            gp.last_prompted_at = None  # clear so reminders don't fire for the next unsent prompt
            session.add(gp)
            session.commit()


def story_exists_by_sid(message_sid: str) -> bool:
    if not message_sid:
        return False
    with open_session() as session:
        return session.exec(
            select(Story).where(Story.twilio_message_sid == message_sid)
        ).first() is not None


def update_story_fields(story_id: int, **fields) -> None:
    """Patch arbitrary fields on a Story row."""
    with open_session() as session:
        story = session.get(Story, story_id)
        if story:
            for k, v in fields.items():
                setattr(story, k, v)
            session.add(story)
            session.commit()


def mark_prompted(grandparent_id: int) -> None:
    """Record that a prompt was just sent so we can track 3-day reminder window."""
    with open_session() as session:
        gp = session.get(Grandparent, grandparent_id)
        if gp:
            gp.last_prompted_at = datetime.now(timezone.utc)
            session.add(gp)
            session.commit()


def get_grandparents_needing_reminder(days: int = 3) -> list[Grandparent]:
    """Return active grandparents prompted >N days ago who haven't replied yet."""
    from datetime import timedelta
    from sqlalchemy import not_, exists
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    with open_session() as session:
        # Single query: grandparents prompted long ago with no story at current prompt_index
        story_exists = (
            select(Story).where(
                Story.grandparent_id == Grandparent.id,
                Story.prompt_index == Grandparent.prompt_index,
            ).exists()
        )
        return list(session.exec(
            select(Grandparent).where(
                Grandparent.active == True,
                Grandparent.last_prompted_at != None,
                Grandparent.last_prompted_at < cutoff,
                not_(story_exists),
            )
        ).all())


def get_family_by_token(token: str) -> Optional["Family"]:
    with open_session() as session:
        return session.exec(
            select(Family).where(Family.timeline_token == token)
        ).first()


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

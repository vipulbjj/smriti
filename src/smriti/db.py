import secrets
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import Index, text
from sqlmodel import Field, Session, SQLModel, create_engine, select

from .config import config


class Language(str, Enum):
    hindi = "hindi"
    english = "english"
    punjabi = "punjabi"


class SubscriptionTier(str, Enum):
    whatsapp = "whatsapp"      # guided chapter sprint
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
    # Set each time a sprint prompt is sent — used for next-day reminders.
    last_prompted_at: Optional[datetime] = Field(default=None)
    # Set when the grandparent gives in-band consent (replies HAAN/YES/ਹਾਂ).
    # None → not yet consented; stories are not saved until this is set.
    consented_at: Optional[datetime] = Field(default=None)


class Story(SQLModel, table=True):
    # One story per grandparent per sprint prompt — a second reply to the same
    # day is rejected gracefully rather than creating a duplicate row.
    # Photo seeds (is_photo_seed=True) live outside this constraint — they're
    # created immediately on photo receipt, ahead of the regular reply that
    # will later land at the same prompt_index.
    __table_args__ = (
        Index(
            "uq_story_gp_prompt_weekly",
            "grandparent_id",
            "prompt_index",
            unique=True,
            sqlite_where=text("is_photo_seed = 0"),
            postgresql_where=text("is_photo_seed = false"),
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    grandparent_id: int = Field(foreign_key="grandparent.id")
    prompt_index: int
    prompt_text: str
    reply_text: str = ""
    enhanced_text: str = ""        # AI-polished prose version of reply_text
    voice_note_url: str = ""
    photo_url: str = ""            # Serves /media/photo/{story_id} after download
    photo_data: Optional[bytes] = Field(default=None)   # Raw photo bytes (permanent, never mutated)
    # --- Photo reconstruction (story-from-image pipeline) ---
    restored_photo_data: Optional[bytes] = Field(default=None)    # Face-repaired + upscaled
    colorized_photo_data: Optional[bytes] = Field(default=None)   # B&W → color
    photo_description: str = ""     # What the vision model literally sees (factual, no invention)
    photo_story_text: str = ""      # AI story *seed* — scaffolding to elicit the real story, never fact
    is_photo_seed: bool = Field(default=False)  # True for photo-only rows outside sprint numbering
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


class DuplicateStoryError(Exception):
    """Raised when a story already exists for this (grandparent_id, prompt_index)."""


def save_story(story: Story) -> Story:
    from sqlalchemy.exc import IntegrityError

    with open_session() as session:
        session.add(story)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            raise DuplicateStoryError(
                f"Story already exists for grandparent {story.grandparent_id} "
                f"day {story.prompt_index}"
            )
        session.refresh(story)
        return story


def advance_prompt(grandparent_id: int) -> None:
    from .program import SPRINT_LENGTH

    with open_session() as session:
        gp = session.get(Grandparent, grandparent_id)
        if gp:
            gp.prompt_index += 1
            if gp.prompt_index >= SPRINT_LENGTH:
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


def mark_consented(grandparent_id: int) -> None:
    """Record in-band consent (grandparent replied HAAN/YES/ਹਾਂ)."""
    with open_session() as session:
        gp = session.get(Grandparent, grandparent_id)
        if gp and gp.consented_at is None:
            gp.consented_at = datetime.now(timezone.utc)
            session.add(gp)
            session.commit()


def grandparent_has_stories(grandparent_id: int) -> bool:
    with open_session() as session:
        return session.exec(
            select(Story).where(Story.grandparent_id == grandparent_id)
        ).first() is not None


def mark_prompted(grandparent_id: int) -> None:
    """Record that a sprint prompt was sent so we can track the reminder window."""
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


def rotate_timeline_token(family_id: int) -> Optional[str]:
    """Issue a fresh timeline_token for a family, invalidating old shared links.
    Returns the new token, or None if the family doesn't exist."""
    with open_session() as session:
        family = session.get(Family, family_id)
        if not family:
            return None
        family.timeline_token = secrets.token_urlsafe(16)
        session.add(family)
        session.commit()
        return family.timeline_token


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

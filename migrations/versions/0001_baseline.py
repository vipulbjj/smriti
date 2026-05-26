"""baseline — schema as it existed before Alembic was introduced

Represents the original Family / Grandparent / Story tables (pre photo-story
pipeline). On an existing production DB whose schema already matches this, run
`alembic stamp 0001` instead of upgrading, then `alembic upgrade head` to apply
later migrations. A fresh DB runs this normally.

Revision ID: 0001
Revises:
Create Date: 2026-05-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "family",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("grandchild_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("grandchild_phone", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("grandchild_email", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("tier", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("notes", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("timeline_token", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "grandparent",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("family_id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("phone", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("language", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("prompt_index", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_prompted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["family_id"], ["family.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "story",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("grandparent_id", sa.Integer(), nullable=False),
        sa.Column("prompt_index", sa.Integer(), nullable=False),
        sa.Column("prompt_text", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("reply_text", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("enhanced_text", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("voice_note_url", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("photo_url", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("photo_data", sa.LargeBinary(), nullable=True),
        sa.Column("audio_url", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("audio_data", sa.LargeBinary(), nullable=True),
        sa.Column("video_job_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("video_url", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("twilio_message_sid", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["grandparent_id"], ["grandparent.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_story_twilio_message_sid", "story", ["twilio_message_sid"])


def downgrade() -> None:
    op.drop_index("ix_story_twilio_message_sid", table_name="story")
    op.drop_table("story")
    op.drop_table("grandparent")
    op.drop_table("family")

"""photo seed rows outside weekly numbering

Adds:
  • Story.is_photo_seed (bool, default false)
  • Replaces the full unique constraint on Story(grandparent_id, prompt_index)
    with a partial unique index that only applies to weekly stories
    (is_photo_seed = false), so a photo seed can occupy the same
    (grandparent_id, prompt_index) slot as the weekly reply that will
    eventually land there.

Batch mode is used for the column add + constraint drop so this works on
SQLite as well as Postgres; `render_as_batch` is already on in
migrations/env.py. The partial index is created outside the batch block
since SQLite's partial-index support isn't reachable through batch ALTER.

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("story") as batch:
        batch.add_column(
            sa.Column("is_photo_seed", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.drop_constraint("uq_story_gp_prompt", type_="unique")

    op.create_index(
        "uq_story_gp_prompt_weekly",
        "story",
        ["grandparent_id", "prompt_index"],
        unique=True,
        sqlite_where=sa.text("is_photo_seed = 0"),
        postgresql_where=sa.text("is_photo_seed = false"),
    )


def downgrade() -> None:
    op.drop_index("uq_story_gp_prompt_weekly", table_name="story")

    with op.batch_alter_table("story") as batch:
        batch.create_unique_constraint("uq_story_gp_prompt", ["grandparent_id", "prompt_index"])
        batch.drop_column("is_photo_seed")

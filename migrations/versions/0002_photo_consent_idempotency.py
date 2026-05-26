"""photo-story columns, consent timestamp, and weekly-prompt idempotency

Adds:
  • Story: restored_photo_data, colorized_photo_data, photo_description, photo_story_text
  • Grandparent: consented_at
  • unique constraint on Story(grandparent_id, prompt_index)

Batch mode is used so the ALTERs and the unique constraint work on SQLite as well
as Postgres. NOTE: if any production rows already violate the uniqueness of
(grandparent_id, prompt_index), de-duplicate them before upgrading or the
constraint creation will fail.

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("story") as batch:
        batch.add_column(sa.Column("restored_photo_data", sa.LargeBinary(), nullable=True))
        batch.add_column(sa.Column("colorized_photo_data", sa.LargeBinary(), nullable=True))
        batch.add_column(sa.Column("photo_description", sqlmodel.sql.sqltypes.AutoString(),
                                   nullable=False, server_default=""))
        batch.add_column(sa.Column("photo_story_text", sqlmodel.sql.sqltypes.AutoString(),
                                   nullable=False, server_default=""))
        batch.create_unique_constraint("uq_story_gp_prompt", ["grandparent_id", "prompt_index"])

    with op.batch_alter_table("grandparent") as batch:
        batch.add_column(sa.Column("consented_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("grandparent") as batch:
        batch.drop_column("consented_at")

    with op.batch_alter_table("story") as batch:
        batch.drop_constraint("uq_story_gp_prompt", type_="unique")
        batch.drop_column("photo_story_text")
        batch.drop_column("photo_description")
        batch.drop_column("colorized_photo_data")
        batch.drop_column("restored_photo_data")

"""Alembic environment — wired to smriti's SQLModel metadata and runtime DB URL.

Batch mode (render_as_batch) is on so ALTER TABLE migrations work on SQLite
(dev) as well as Postgres (prod).
"""

from logging.config import fileConfig

from alembic import context
from sqlmodel import SQLModel

# Import the models so their tables register on SQLModel.metadata.
from smriti import db as _db  # noqa: F401
from smriti.config import config as smriti_config

alembic_config = context.config

if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)

target_metadata = SQLModel.metadata


def _url() -> str:
    return smriti_config.database_url


def run_migrations_offline() -> None:
    context.configure(
        url=_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    from sqlalchemy import create_engine

    connect_args = {"check_same_thread": False} if _url().startswith("sqlite") else {}
    engine = create_engine(_url(), connect_args=connect_args)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

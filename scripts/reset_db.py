"""
Fresh-recreate the database: drop all tables, then apply Alembic migrations.

DESTRUCTIVE — drops every smriti table. Intended for the stealth-mode case where
there is no data to keep. Refuses to run without an explicit --yes flag and prints
the (password-redacted) target so you can confirm you're pointed at the right DB.

Usage:
    DATABASE_URL='postgresql://...prod...' uv run python scripts/reset_db.py --yes

After it runs, the schema is at Alembic head (0001 + 0002) with an
`alembic_version` table, so future migrations work normally.
"""

import argparse
import re
import sys


def redact(url: str) -> str:
    """Hide the password in a DB URL for safe printing."""
    return re.sub(r"(://[^:/@]+:)[^@]+(@)", r"\1***\2", url)


def main(argv: list[str]) -> int:
    import os

    parser = argparse.ArgumentParser(description="Drop all tables and re-run migrations.")
    parser.add_argument("--yes", action="store_true", help="confirm the destructive reset")
    args = parser.parse_args(argv)

    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        print("ERROR: DATABASE_URL is not set. Refusing to run.", file=sys.stderr)
        return 2

    print(f"Target database: {redact(db_url)}")
    if not args.yes:
        print("Refusing to drop tables without --yes. Re-run with --yes to proceed.",
              file=sys.stderr)
        return 1

    # Heavy imports only after the guards pass.
    from sqlmodel import SQLModel
    import smriti.db as db  # registers models on SQLModel.metadata

    engine = db.get_engine()
    print("Dropping all smriti tables…")
    SQLModel.metadata.drop_all(engine)

    # Also drop alembic_version if a previous run left one, so upgrade starts clean.
    from sqlalchemy import text
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))

    print("Applying migrations to head…")
    from alembic import command
    from alembic.config import Config

    command.upgrade(Config("alembic.ini"), "head")
    print("Done. Schema is at Alembic head.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

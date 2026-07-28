"""
Preflight check for Alembic migration 0003 (photo seeds + partial unique index).

READ-ONLY. Touches no data. Run it against a copy of prod (or prod itself) before
`alembic upgrade head` to confirm 0003 will apply cleanly.

0003 does three things that depend on the live schema:
  1. adds Story.is_photo_seed
  2. drops the existing unique constraint BY NAME (`uq_story_gp_prompt`)
  3. creates a partial unique index `uq_story_gp_prompt_weekly`

Step 2 is the risk: if the live constraint has a different name (or was never
created as a named constraint), the drop fails and the migration aborts. This
script reports the actual constraint name so you know before you run it.

Usage:
    DATABASE_URL='postgresql://...prod...' uv run python scripts/preflight_0003.py

Exit code 0 = safe to migrate. Non-zero = look at the report before migrating.
"""

import os
import re
import sys

from sqlalchemy import create_engine, inspect, text

EXPECTED_DROP_NAME = "uq_story_gp_prompt"
NEW_INDEX_NAME = "uq_story_gp_prompt_weekly"
TARGET_COLUMNS = ["grandparent_id", "prompt_index"]


def redact(url: str) -> str:
    """Hide the password in a DB URL for safe printing."""
    return re.sub(r"(://[^:/@]+:)[^@]+(@)", r"\1***\2", url)


def _weekly_slot_constraint(inspector) -> tuple[str | None, str]:
    """Find whatever enforces uniqueness on (grandparent_id, prompt_index) today.

    Returns (name, kind) where kind is 'constraint', 'index', or 'none'.
    """
    for uc in inspector.get_unique_constraints("story"):
        if list(uc.get("column_names") or []) == TARGET_COLUMNS:
            return uc.get("name"), "constraint"
    for ix in inspector.get_indexes("story"):
        if ix.get("unique") and list(ix.get("column_names") or []) == TARGET_COLUMNS:
            return ix.get("name"), "index"
    return None, "none"


def _alembic_version(engine) -> str | None:
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT version_num FROM alembic_version")).first()
            return row[0] if row else None
    except Exception:
        return None


def _duplicate_slots(engine, has_seed_column: bool) -> list[tuple]:
    """Rows that would violate a unique (grandparent_id, prompt_index) among the
    stories the partial index will still cover. If is_photo_seed already exists,
    exclude seeds the way the new index does."""
    where = "WHERE is_photo_seed = false" if has_seed_column else ""
    sql = text(
        f"""
        SELECT grandparent_id, prompt_index, COUNT(*) AS n
        FROM story
        {where}
        GROUP BY grandparent_id, prompt_index
        HAVING COUNT(*) > 1
        ORDER BY n DESC
        """
    )
    with engine.connect() as conn:
        return [tuple(r) for r in conn.execute(sql).all()]


def main() -> int:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL is not set. Point it at the DB you want to check.")
        return 2

    print(f"Target DB: {redact(url)}")
    engine = create_engine(url)
    inspector = inspect(engine)

    if "story" not in inspector.get_table_names():
        print("No `story` table found. Is this the right database?")
        return 2

    columns = {c["name"] for c in inspector.get_columns("story")}
    has_seed_column = "is_photo_seed" in columns
    version = _alembic_version(engine)
    name, kind = _weekly_slot_constraint(inspector)
    already_migrated = any(
        ix.get("name") == NEW_INDEX_NAME for ix in inspector.get_indexes("story")
    )

    print(f"Alembic version:   {version or 'unknown (no alembic_version row)'}")
    print(f"is_photo_seed col: {'present' if has_seed_column else 'absent'}")
    print(f"weekly-slot uniqueness: {kind} named {name!r}")
    print(f"partial index {NEW_INDEX_NAME!r}: {'present' if already_migrated else 'absent'}")

    problems = []

    if already_migrated and has_seed_column:
        print("\nLooks like 0003 is already applied. Nothing to do.")
        return 0

    if kind == "none":
        problems.append(
            "No unique constraint/index on (grandparent_id, prompt_index) found. "
            "0003's drop step will fail. Reconcile the schema first."
        )
    elif name != EXPECTED_DROP_NAME:
        problems.append(
            f"The weekly-slot uniqueness is named {name!r}, but 0003 drops "
            f"{EXPECTED_DROP_NAME!r} by name. Edit 0003 to drop {name!r}, or rename "
            f"the constraint in prod, before migrating."
        )

    dupes = _duplicate_slots(engine, has_seed_column)
    if dupes:
        shown = ", ".join(f"gp={g} idx={i} x{n}" for g, i, n in dupes[:5])
        problems.append(
            f"{len(dupes)} duplicate (grandparent_id, prompt_index) group(s) among "
            f"weekly stories: {shown}{' ...' if len(dupes) > 5 else ''}. The new partial "
            "index would reject these. De-dupe before migrating."
        )

    if problems:
        print("\nNOT SAFE YET:")
        for p in problems:
            print(f"  - {p}")
        return 1

    print("\nSafe to migrate. Run: uv run alembic upgrade head")
    return 0


if __name__ == "__main__":
    sys.exit(main())

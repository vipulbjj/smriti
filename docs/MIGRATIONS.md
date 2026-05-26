# Database migrations (Alembic)

Smriti uses Alembic for schema changes. `create_all()` only ever *adds missing
tables* — it never alters an existing table — so every column, index, or
constraint change after the first deploy must be a migration.

## Adding the next migration

1. **Change the models** in `src/smriti/db.py` (add a column, index, constraint…).

2. **Generate the migration** by diffing the models against a DB that is already
   at `head`:
   ```bash
   # use a scratch DB at head so autogenerate only sees YOUR change
   rm -f /tmp/mig.db
   DATABASE_URL="sqlite:////tmp/mig.db" uv run alembic upgrade head
   DATABASE_URL="sqlite:////tmp/mig.db" uv run alembic revision --autogenerate -m "describe the change"
   ```
   Autogenerate is a *draft* — always open the new file in `migrations/versions/`
   and read it. SQLModel string columns render as `sqlmodel.sql.sqltypes.AutoString`;
   keep that.

3. **Make it SQLite-safe.** SQLite can't `ALTER`/drop columns or add constraints
   in place, so wrap table edits in batch mode:
   ```python
   with op.batch_alter_table("story") as batch:
       batch.add_column(sa.Column("new_col", sa.String(), nullable=False, server_default=""))
   ```
   `render_as_batch=True` is already set in `migrations/env.py`, so autogenerate
   emits batch blocks — but hand-written edits must use them too. Give every new
   NOT NULL column a `server_default` so existing rows backfill cleanly.

4. **Test it both directions** on a scratch DB:
   ```bash
   rm -f /tmp/mig.db
   DATABASE_URL="sqlite:////tmp/mig.db" uv run alembic upgrade head      # applies
   DATABASE_URL="sqlite:////tmp/mig.db" uv run alembic downgrade -1      # reverts
   DATABASE_URL="sqlite:////tmp/mig.db" uv run alembic upgrade head      # re-applies
   ```
   Then confirm the migrated schema matches the models (a fresh `create_all` DB
   should have identical columns).

5. **Commit** the new `migrations/versions/00NN_*.py` with the model change.

## Applying to production

Production (Postgres on Vercel) is the source of truth — apply with care:
```bash
export DATABASE_URL='<prod postgres url>'   # double-check the host!
uv run alembic upgrade head
uv run alembic current                      # should print the new head
```

If a migration adds a UNIQUE constraint, de-duplicate offending rows first or the
constraint creation fails.

## Hand-writing vs autogenerate

Autogenerate is convenient but misses some changes (CHECK constraints, server
defaults, enum value changes, data migrations). For anything non-trivial,
hand-write the `upgrade()`/`downgrade()` — it's just `op.add_column`,
`op.create_index`, `op.create_unique_constraint`, etc. Migrations `0001`/`0002`
are hand-written and a good template.

## Note on `create_all()` at startup

`main.py` still calls `init_db()` (`create_all`) on boot. It's harmless alongside
Alembic — it no-ops on existing tables — but it means a brand-new deploy creates
tables without an `alembic_version` row. After any fresh DB creation, run
`alembic stamp head` so Alembic knows the current state. (The `scripts/reset_db.py`
fresh-recreate path handles this for you by running `upgrade head`.) Eventually,
consider dropping `init_db()` from startup and relying on Alembic alone.

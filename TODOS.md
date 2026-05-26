# smriti — Outstanding TODOs

Items deferred from the May 2026 engineering review. Updated 2026-05-26 after the
hardening pass — most items are now done; remaining work is noted at the bottom.

---

## P1 — Before scaling to >10 families

### ✅ Alembic database migrations — DONE
Alembic is set up (`alembic.ini`, `migrations/`). `0001` is the pre-existing
schema baseline; `0002` adds the photo-story columns, `consented_at`, and the
`(grandparent_id, prompt_index)` unique constraint. Batch mode is on so ALTERs
work on SQLite and Postgres.

**Runbook:**
- Fresh DB: `uv run alembic upgrade head`.
- Existing production DB (schema already matches the baseline): `uv run alembic
  stamp 0001` once, then `uv run alembic upgrade head` to apply `0002`.
- ⚠️ Before `0002` on prod: de-duplicate any rows that violate
  `(grandparent_id, prompt_index)` or the unique-constraint creation will fail.

### ✅ PDF object storage (Vercel compatibility) — DONE
`book.generate_book()` now routes through `storage.store_pdf()`: uploads to S3/R2
and returns a signed URL when `STORAGE_BUCKET` is configured, else returns the
local path (zero-setup local dev). Needs the `storage` extra (`boto3`) + bucket
creds to activate in prod.

### ✅ Prompt idempotency guard (week-level dedup) — DONE
Unique constraint on `Story(grandparent_id, prompt_index)`; `save_story` raises
`DuplicateStoryError` and the webhook replies "we've already saved your answer
this week" instead of 500ing.

---

## P2 — Trust & legal

### ✅ Consent form / opt-in flow — DONE
`Grandparent.consented_at` added. An unconsented grandparent's first message must
be an affirmative (HAAN / YES / ਹਾਂ / ji / ठीक है …) before any story is saved;
otherwise a consent request is sent. Legacy grandparents who already have stories
are auto-grandfathered.

### ✅ Timeline token revocation — DONE
`POST /admin/api/rotate-token/{family_id}` issues a fresh `timeline_token` and
invalidates old shared links (`db.rotate_timeline_token`).

---

## P3 — Nice to have

### ✅ Landing page copy accuracy (D9) — ALREADY ACCURATE
The current "sprint" landing copy already reflects that the grandchild signs up:
hero — "Your grandparent replies by voice on WhatsApp"; Step 1 — "You start the
sprint / Tell us their name…"; CTA — "Gift it". No change needed.

### ✅ Rate-limit protection on webhook — DONE
Per-phone in-memory token bucket (`ratelimit.py`, default 10 msg/hour) guards the
webhook. Best-effort on serverless (resets on cold start); swap for Redis if a
hard cross-instance limit is needed.

---

## Still open

- **Redis-backed rate limit** — only if a hard limit across serverless instances
  is required; the in-memory bucket is sufficient at current scale.
- **Run `0002` against the live DB** — follow the runbook above once the PR merges.

# smriti — Outstanding TODOs

Items deferred from the May 2026 engineering review. Each has a brief rationale.

---

## P1 — Before scaling to >10 families

### Alembic database migrations
SQLModel's `create_all()` only creates missing tables on a fresh DB. Any schema
change (new column, new index) on an existing production DB requires a migration.
Set up Alembic with an autogenerate baseline from the current models before the
first production data lands, so schema evolution is safe.

### PDF object storage (Vercel compatibility)
`generate_pdf()` in `book.py` writes to a local temp path. On Vercel, `/tmp` is
ephemeral and the 250 MB limit makes large PDFs risky. Move generated PDFs to S3
or Cloudflare R2 and return a signed download URL instead of streaming bytes.

### Prompt idempotency guard (week-level dedup)
The webhook deduplicates by `MessageSid` but a grandparent can reply multiple times
in the same week if they reply to an older WhatsApp thread. Add a DB-level unique
constraint on `(grandparent_id, prompt_index)` so the second reply is rejected
gracefully (send a polite "already received your answer this week" message instead
of a 500).

---

## P2 — Trust & legal

### Consent form / opt-in flow
Currently grandparents are enrolled by the grandchild with no in-band consent
step. Add a first-message consent prompt: grandparent must reply "HAAN" / "YES" /
"ਹਾਂ" before their first story is saved. Store `consented_at` on `Grandparent`.

### Timeline token revocation
`Family.timeline_token` is a permanent URL. Add an admin endpoint to rotate the
token (invalidates old shared links) and expose it in the admin dashboard.

---

## P3 — Nice to have

### Landing page copy accuracy (D9 from CEO review)
Current landing page implies the grandparent registers. Fix sub-text and the
"How it works" Step 1 copy to accurately reflect that the grandchild signs up and
the grandparent just replies to WhatsApp messages.

### Rate-limit protection on webhook
A malicious actor who knows a grandparent's WhatsApp number could flood the webhook
(Twilio signature validation only catches non-Twilio senders). Add a per-phone
rate limit (e.g. 10 messages/hour) using a Redis counter or an in-memory token
bucket on non-Vercel deployments.

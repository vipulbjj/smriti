# Spec: photo → personalized prompt

Status: ready to build. Author: build session, 2026-07-21.
First slice of the `story-from-image` flagship (`STRATEGY_2026.md` §3). Ships on the
current Twilio path, no Meta dependency, no new infra.

## Problem

When a grandparent sends an old photo over WhatsApp today, the webhook treats it like
a weekly reply: it saves a `Story` against the current `prompt_index`, sets
`reply_text = "📷"` when there's no caption, and calls `advance_prompt()`. So the photo
silently burns a weekly prompt slot and no actual story gets attached to it. The
grandparent gets the generic acknowledgement and nothing pulls the story out of them.

## Outcome

A photo becomes a conversation starter. Smriti looks at the photo and replies with a
warm, specific question about *that image* in the grandparent's language, instead of the
generic weekly prompt. The photo is stored (already happens) and the vision model's
factual description is saved to `Story.photo_description` for the later restore/colorize
pipeline. The weekly prompt counter is **not** advanced by a photo, so the sprint
cadence stays intact.

Success criteria:
- Sending a photo (no caption) returns a photo-specific prompt, not the "📷 saved" ack.
- `Story.photo_description` is populated with what the model literally sees (no invention).
- `advance_prompt()` is NOT called for a photo-only message.
- If the caption is a real story (>= 15 chars), current weekly-reply behaviour is
  unchanged (still saved and counted). Photo + long caption = normal story that also
  carries the photo.
- Groq unavailable or vision call fails → graceful fallback to today's behaviour
  (store photo, send a friendly generic prompt, never 500).

## Scope

In: the vision call, the photo-specific prompt generation, webhook rewiring for the
photo-only branch, tests.

Out (later slices): face restore (GFPGAN), upscale (Real-ESRGAN), colorize (DeOldify),
animation. Those need GPU hosting and are tracked separately. This slice touches none of
`restored_photo_data` / `colorized_photo_data`.

## Design

### 1. `ai.py` — add a vision function

Groq serves a vision-capable Llama (e.g. `llama-3.2-11b-vision-preview` / the current
vision model id — confirm against the Groq model list at build time; keep it in
`config.py`, not hard-coded in feature code). Reuse the existing `_get_groq()` client.

```python
def describe_and_prompt_photo(
    photo_bytes: bytes,
    grandparent_name: str,
    language: str = "hindi",
) -> tuple[str, str] | None:
    """Returns (photo_description, personalized_prompt), or None if unavailable.

    photo_description: strictly what the model sees — people, setting, era cues,
                       objects. No invented backstory. Feeds the restore pipeline
                       and the memoir.
    personalized_prompt: one warm question in `language` that invites the
                         grandparent to tell the story behind the photo.
    """
```

Implementation notes:
- Encode `photo_bytes` as a base64 data URL for the vision message content.
- Two asks in one call (return strict JSON with `description` and `prompt` keys) to
  keep it to a single request, or two small calls if JSON reliability is poor on the
  8b-class model. Prefer one call; parse defensively.
- The prompt-generation instruction must be language-aware (Hindi / English / Punjabi),
  warm, and elicitation-style ("Tell me about this day. Who is next to you?"), matching
  the tone in `prompts.py`. Address the grandparent by `grandparent_name`.
- Hard rule for the description half: factual only, no invented names/dates. This mirrors
  the existing `photo_description` vs `photo_story_text` split in `db.py`.
- Return `None` on any failure so the caller can fall back.

### 2. `webhook.py` — rewire the image branch

Current image handling is inside the main story-save path. Split it so a **photo-only**
message (image with no substantive caption) is its own branch that runs *before* the
"guard: don't save trivial replies" check and does not advance the prompt.

New flow when `num_media > 0` and content type is image:
1. Download photo into `photo_data` (unchanged).
2. If the caption is a real story (>= 15 chars): keep today's behaviour — save as the
   weekly story with the photo attached, advance prompt, ack. Done.
3. Else (photo-only): call `describe_and_prompt_photo(photo_data, gp.name, gp.language)`.
   - Save a `Story` with `is_photo_seed = True` carrying `photo_data`, `photo_url`,
     `photo_description`, and the generated prompt in `photo_story_text`. Do **not** call
     `advance_prompt()` — a photo does not consume a weekly slot.
   - **DECIDED (do not relitigate): photo seeds live outside the weekly numbering via an
     `is_photo_seed` boolean + a partial unique index (see Data/migration below).** Do NOT
     reuse the current weekly slot with `prompt_index = gp.prompt_index` under the existing
     full unique constraint — that collides with the grandparent's real weekly reply and
     drops their story via `DuplicateStoryError`. On the primary revenue product, silent
     data loss is unacceptable; the migration is the correct cost.
   - Reply to the grandparent with `personalized_prompt`.
   - On `None`/failure: fall back to storing the photo and sending the generic weekly
     prompt (never the bare "📷 saved" dead-end).

### 3. Config

Add `GROQ_VISION_MODEL` to `config.py` (default to the current Groq vision model id).
Access only via `Config`, never `os.environ` in feature code (house rule).

## Data / migration (Alembic 0003 — required)

`photo_description` and `photo_story_text` already exist on `Story`. This feature adds:

1. `is_photo_seed: bool` column on `Story`, default `False` (nullable boolean is fine;
   treat `NULL`/`False` as "weekly story").
2. Replace the existing full unique constraint `uq_story_gp_prompt`
   (`grandparent_id`, `prompt_index`) with a **partial** unique index that applies only
   to weekly stories: unique on `(grandparent_id, prompt_index) WHERE is_photo_seed = false`.
   Both Postgres and SQLite (>= 3.8) support partial indexes. This lets a photo seed carry
   any `prompt_index` (including the current week's) without colliding with the real reply.

Alembic revision `0003`, batch mode already on. Migration steps: add column, drop old
`UniqueConstraint`, create the partial unique index. Update the `Story` model's
`__table_args__` accordingly (SQLModel: use `Index(..., unique=True, sqlite_where=..., postgresql_where=...)`
or an equivalent `DDL`/`sa.Index` with a `.where()` clause). Include a downgrade that
restores the full unique constraint.

Note the runbook already established for prod: dedupe before applying, `alembic upgrade
head`. `0003` here only relaxes a constraint and adds a column, so it won't fail on
existing rows.

## Tests (ship with the feature)

- Photo-only message → `describe_and_prompt_photo` called, personalized prompt sent,
  `advance_prompt` NOT called, `photo_description` saved. (Mock the Groq client.)
- Photo + long caption → normal weekly story saved with photo, prompt advanced.
- Groq unavailable → fallback path: photo stored, generic prompt sent, no crash, no 500.
- Vision returns malformed JSON → parsed defensively, falls back cleanly.
- Rate limit / consent gates still fire before any of this (regression).

## Risks

- Vision JSON reliability on a small model. Mitigation: defensive parsing + fallback.
- Hindi/Punjabi prompt quality from the vision model. Mitigation: keep the
  prompt-generation instruction explicit about language and tone; spot-check real
  outputs before enabling in prod. If quality is poor, generate the description in
  English via vision, then reuse the existing text Llama in `enhance_story`-style to
  render the question in the target language.
- Groq free-tier request budget: this adds one vision call per inbound photo. Fine at
  current scale (well under the 14.4K/day free limit).

## Estimate

Half a day. One new `ai.py` function, one webhook branch split, one config line,
~5 tests. No infra, no new vendor.

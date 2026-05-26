# smriti — CLAUDE.md

## What this is

WhatsApp-native memoir service for Indian families: grandparents receive one story prompt per week via WhatsApp, reply by text or voice note, and the year's responses compile into a printed PDF memoir book. Supports Hindi, English, and Punjabi.

**This is the primary revenue project. Treat it with extra care — correctness and reliability over speed.**

## Stack

- **Framework**: FastAPI (Twilio webhook receiver + admin API)
- **Language**: Python 3.11+
- **Styling**: None (backend only; HTML landing page rendered inline from `src/smriti/landing.py`)
- **DB**: SQLite locally via SQLModel; Postgres in production (set `DATABASE_URL`)
- **Auth**: No user auth — Twilio signature validation secures the webhook
- **Hosting**: Vercel (Python build via `@vercel/python`, entry: `api/index.py`)
- **Package manager**: uv (always use `uv run`, never bare `python`)
- **Other notable libs**: Twilio WhatsApp API, OpenAI Whisper / Groq (transcription), APScheduler, ReportLab (PDF), ElevenLabs (TTS), gTTS, Shotstack (video), Pillow

## Commands

```bash
# Install
uv sync

# Dev server
uv run uvicorn smriti.main:app --reload
# Expose to Twilio: ngrok http 8000
# Set Twilio webhook to: https://<ngrok-url>/webhook/whatsapp

# Tests
uv run pytest

# Admin CLI
uv run python -m smriti.admin list
uv run python -m smriti.admin add-family
uv run python -m smriti.admin stories --family-id <id>
uv run python -m smriti.admin send-prompt --grandparent-id <id>
uv run python -m smriti.admin generate-book --family-id <id>
```

No lint or typecheck scripts yet — TODO: add ruff + mypy.

## Project structure

```
src/smriti/
├── config.py       All env vars — access only via Config class, never os.environ directly
├── db.py           SQLModel models + DB session helpers
├── webhook.py      FastAPI route for inbound WhatsApp messages
├── scheduler.py    APScheduler weekly job (Monday 9 AM IST prompts)
├── book.py         PDF memoir generator (ReportLab)
├── admin.py        CLI admin commands
├── admin_web.py    Web admin interface
├── ai.py           AI utilities
├── transcribe.py   Voice note transcription (OpenAI Whisper or Groq)
├── whatsapp.py     Twilio WhatsApp client
├── prompts.py      52 weekly prompts in Hindi / English / Punjabi
├── tts.py          Text-to-speech (ElevenLabs / gTTS)
├── video.py        Video generation (Shotstack)
├── timeline.py     Story timeline
├── landing.py      Landing page HTML
├── cron.py         Vercel cron job endpoints
├── commands.py     WhatsApp command handling
├── index.py        Module index
└── main.py         FastAPI app + lifespan startup
api/
└── index.py        Vercel Python entry point (all routes forwarded here)
tests/              pytest test suite (db, webhook, book, prompts, commands, cron)
books/              Generated PDF books (gitignored — ensure dir exists)
```

Important files:
- `src/smriti/config.py` — all settings; never call `os.environ.get()` in feature code
- `api/index.py` — Vercel entry point; changes here affect production routing
- `vercel.json` — cron schedule + build config

## Conventions

- **Package manager**: always `uv run` — never bare `python` or `pip`
- **Env vars**: access only via `Config` class in `config.py`
- **Transcription**: configurable via `TRANSCRIPTION_PROVIDER` env var (`"groq"` for free tier, `"openai"` for quality)
- **Languages**: Hindi, English, Punjabi — prompts in `prompts.py` cover all three
- **No web UI** except the landing page — this is a WhatsApp-native product

## Git workflow

- Branches: `vipul/<short-description>` for solo work
- Commit style: conventional commits (`feat:`, `fix:`, `chore:`)
- No CI configured yet — TODO: add GitHub Actions for `uv run pytest`

## Deploy

- Vercel auto-deploys on push to `main` via `@vercel/python` build
- Cron jobs in `vercel.json`:
  - `/cron/send-prompts` — Mon 3:30 UTC (= Mon 9 AM IST)
  - `/cron/send-reminders` — Thu 3:30 UTC (= Thu 9 AM IST)
  - `/cron/poll-videos` — daily noon UTC
  - `/cron/process-pending` — daily 4 AM UTC
- Env vars (Vercel dashboard): `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM`, `OPENAI_API_KEY`, `GROQ_API_KEY`, `ELEVENLABS_API_KEY`, `SHOTSTACK_API_KEY`, `DATABASE_URL`, `WEBHOOK_BASE_URL`, `CRON_SECRET`, `ADMIN_KEY`, `TRANSCRIPTION_PROVIDER`

## Database

SQLModel + SQLite (dev) / Postgres (prod via `DATABASE_URL`).
- Schema applied via SQLModel `create_all()` at app startup — no migration tool yet
- TODO: add Alembic for proper migration management

## Testing philosophy

- pytest + pytest-asyncio
- Tests in `tests/` covering: db, webhook, book, prompts, commands, cron
- New features ship with at least one test. Bug fixes ship with a regression test.

## Things that are out of scope

- TODO: Vipul, anything explicitly off-limits for smriti right now?

## Known gotchas

- Twilio signature validation is on by default (`VALIDATE_TWILIO_SIGNATURE=true`). Disabling in prod is a security risk — only disable for local dev.
- `books/` directory must exist before `generate-book` runs — it's gitignored, so create manually in prod if needed.
- Cron times in `vercel.json` are UTC — Monday 3:30 UTC = Monday 9 AM IST.
- ElevenLabs voice IDs are hardcoded defaults in `config.py` — override via env vars after manual voice setup in ElevenLabs dashboard.

## Product context (for non-code tasks)

- **Audience**: Indian families — adult children (30s–40s) buying the service to preserve their grandparents' stories
- **Pricing**: WhatsApp tier ₹15,000/yr; Concierge ₹25,000; AI Vault ₹50,000–₹1,50,000
- **Voice**: Warm, emotional, and deeply familial — this product touches grief, memory, and love, so every word matters. But it's also startup-forward: energetic, mission-driven, proud of what it's building. Support replies should feel personal and heartfelt, never clinical. Never make light of what families are preserving.
- **Recently shipped**: See `TODOS.md` for deferred work
- **What we'd never say**: TODO — any phrases or approaches to avoid?

## Decision log

Log significant architectural decisions here so they're not relitigated.

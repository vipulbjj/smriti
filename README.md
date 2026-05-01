# smriti (स्मृति)

WhatsApp-native story collection for grandparents. One question a week, 52 weeks, one printed memoir.

## What it does

1. Every Monday 9 AM IST, sends a prompt to registered grandparents via WhatsApp.
2. Grandparents reply by text or voice note. Voice notes are transcribed via OpenAI Whisper.
3. Stories accumulate in a SQLite database.
4. Generate a formatted PDF memoir book any time with `smriti.admin generate-book`.

Languages: Hindi, English, Punjabi.

## Stack

- **FastAPI** — Twilio webhook receiver
- **SQLModel + SQLite** — zero-ops storage
- **Twilio WhatsApp API** — messaging
- **OpenAI Whisper** — voice note transcription
- **APScheduler** — weekly cron (Monday 9 AM IST)
- **ReportLab** — PDF generation

## Setup

```bash
cp .env.example .env
# Fill in TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, OPENAI_API_KEY
uv sync
uv run python -m smriti.admin add-family
```

## Run

```bash
uv run uvicorn smriti.main:app --reload
# Expose with: ngrok http 8000
# Set Twilio webhook URL to: https://<ngrok-url>/webhook/whatsapp
```

## Admin CLI

```bash
uv run python -m smriti.admin list
uv run python -m smriti.admin add-family
uv run python -m smriti.admin stories --family-id 1
uv run python -m smriti.admin send-prompt --grandparent-id 1
uv run python -m smriti.admin generate-book --family-id 1
```

## Tests

```bash
uv run pytest
```

## Project structure

```
src/smriti/
  config.py      env vars
  db.py          SQLModel models + DB helpers
  prompts.py     52 weekly prompts (Hindi / English / Punjabi)
  whatsapp.py    Twilio client
  transcribe.py  OpenAI Whisper
  webhook.py     FastAPI route for inbound WhatsApp
  scheduler.py   APScheduler weekly job
  book.py        PDF memoir generator
  admin.py       CLI
  main.py        FastAPI app + lifespan
```

## Pricing model

| Tier | Price | What they get |
|---|---|---|
| WhatsApp | ₹15,000/yr | 52 weekly prompts, voice transcription, PDF book |
| Concierge | ₹25,000 | In-person recorded session + edited memoir |
| AI Vault | ₹50,000–₹1,50,000 | Voice clone, photo animation, multilingual memoir |

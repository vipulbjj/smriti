# How the vertical repos connect to Smriti

Answering the design question directly: **API / HTTP for the compute-heavy
services, in-process library import for the transport adapter, env-var provider
selection as the glue. Not MCP for the product runtime.** Here's the reasoning
and the per-vertical decision.

---

## TL;DR decision table

| Vertical repo | Connection style | How Smriti selects it | Why |
|---|---|---|---|
| `smriti-whisper` (transcription) | **HTTP service** | `TRANSCRIPTION_PROVIDER=huggingface` + `WHISPER_SERVICE_URL` | needs a GPU; deployed separately |
| `smriti-voice` (XTTS cloning) | **HTTP service** | `VOICE_SERVICE_URL` + stored `voice_model_url` | GPU + heavy `torch`/`TTS` deps |
| photo restoration | **HTTP service** | `REPLICATE_API_TOKEN` or `RESTORE_SERVICE_URL` | GPU models (GFPGAN/DeOldify) |
| `smriti-reel` (story→video) | **HTTP service** *or* in-proc ffmpeg | `VIDEO_PROVIDER` + `REEL_SERVICE_URL` | illustration needs GPU; ffmpeg can be local |
| `smriti-whatsapp-meta` (transport) | **in-process library** | `WHATSAPP_PROVIDER=meta` | it *is* the webhook — must run in Smriti's process |

---

## Why HTTP, not MCP, for the runtime

**MCP (Model Context Protocol) is for exposing tools to an LLM agent.** It assumes
an agent loop deciding which tool to call. Smriti's runtime is **not** an agent —
it's a deterministic pipeline: a WhatsApp webhook fires → transcribe → store →
enhance → (later) restore/animate. Each step is a known, ordered service call, not
a choice an LLM makes at runtime.

Putting MCP in that path would add an LLM/agent indirection layer to plain
request/response calls — more latency, more failure modes, more cost, no benefit.
So for the product, the verticals are **ordinary HTTP microservices** (or library
imports), wired by config.

**Where MCP *would* earn its place — later, and separately:** an internal
**ops/admin agent**. If you want to ask, in natural language, "regenerate Dadi's
week-12 video," "which families stalled this week," or "rebuild this book," then
wrapping the admin actions as MCP tools so Claude can orchestrate them is a great
fit. That's a back-office convenience layer, *not* the customer pipeline. Build it
only when manual ops gets painful.

---

## The pattern: env-var-selected providers

Smriti core defines a small **interface** per capability; an env var picks the
implementation. The reference is already in the code — `transcribe.py`:

```python
def transcribe(audio_bytes, language="hindi") -> str:
    if provider == "huggingface" and config.whisper_service_url:
        result = _transcribe_service(...)   # HTTP → smriti-whisper
        if result is not None: return result
        # falls back ↓ so a voice note is never lost
    if provider == "openai": ...
    return transcribe_groq(...)             # default
```

Every vertical follows this shape:
1. A capability function in Smriti core (`transcribe`, `synthesize`, `restore`,
   `make_reel`, `send_message`).
2. An env var chooses local-default vs deployed-service.
3. The service is called over HTTP with a **shared-secret key** (`*_API_KEY`).
4. **Graceful fallback** — if the service is unreachable, fall back to the hosted
   default rather than failing the whole webhook. (This is the standing convention:
   every provider degrades to a safe default.)

```
        WhatsApp message
              │
        ┌─────▼───────────────── Smriti core (Vercel) ─────────────────┐
        │  webhook → providers selected by env vars                    │
        │     transcribe()  ── HTTP ──►  smriti-whisper   (GPU host)   │
        │     synthesize()  ── HTTP ──►  smriti-voice     (GPU host)   │
        │     restore()     ── HTTP ──►  restoration svc  (GPU host)   │
        │     make_reel()   ── HTTP/local ──► smriti-reel              │
        │     send_message()── import ──► smriti-whatsapp-meta (in-proc)│
        └──────────────────────────────────────────────────────────────┘
```

### Why the transport adapter is different (in-process)

`smriti-whatsapp-meta` is the *webhook itself* and the send/download functions
Smriti calls inline. It has no GPU need and must share the request context, so it's
a **Python package Smriti imports** (pip-install from the git repo or vendor it),
selected by `WHATSAPP_PROVIDER=meta`. Making it a separate HTTP hop would be pure
overhead.

---

## Deploying the services

- **Where:** Modal, a Hugging Face Space (GPU), Fal, or a rented GPU box. Each repo
  has a `Dockerfile` / deploy note.
- **Auth:** a shared secret per service (`WHISPER_API_KEY`, `VOICE_API_KEY`, …),
  set both on the service and in Smriti's env. Services reject mismatched keys.
- **Config lives in env, not code:** Smriti holds only URLs + keys (Vercel
  dashboard). No vertical is a hard dependency — unset its URL and Smriti uses the
  hosted/local default.
- **One service per capability, called directly.** No central gateway — at 5
  services that's needless ops. Revisit a gateway only if cross-cutting concerns
  (auth, rate limiting, observability) start being duplicated.

---

## What this means for "ship with the product according to PMF"

You can light up each vertical independently, in priority order, with a single env
var — no big-bang integration. Ship Smriti core as-is; when a GPU host is ready,
point `WHISPER_SERVICE_URL` at it and transcription goes self-hosted with zero code
change. Same for voice, photos, video. The product never blocks on a vertical being
ready, and every vertical can also be sold/run standalone.

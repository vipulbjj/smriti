---
title: Whisper Transcription Service
emoji: 🎙️
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
suggested_hardware: t4-small
---

# Whisper Transcription Service

A self-hosted FastAPI microservice for transcribing uploaded audio files with OpenAI's Whisper Large v3 model from Hugging Face Transformers.

## Transcribe Audio

Send a `POST` request to `/transcribe` using `multipart/form-data` with an audio file field named `file`.

The API returns JSON with the transcript text and detected language:

```json
{
  "transcript": "the transcribed text here",
  "language": "english"
}
```

## Example Curl

```bash
curl -X POST "https://YOUR-SPACE-NAME.hf.space/transcribe" \
  -F "file=@audio.mp3"
```

For local testing:

```bash
curl -X POST "http://localhost:7860/transcribe" \
  -F "file=@audio.mp3"
```

## Tech Stack

- FastAPI
- Uvicorn
- Hugging Face Transformers
- PyTorch CUDA (cu121)
- Accelerate
- Docker

## Run Locally

Prerequisites: Python 3.11+ (3.12 works), ~3 GB disk for dependencies, and several GB more on first run while Whisper weights download from Hugging Face.

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 7860 --reload
```

First startup loads `openai/whisper-large-v3` into memory and can take several minutes on CPU. Check readiness:

```bash
curl http://127.0.0.1:7860/
```

Then transcribe:

```bash
curl -X POST "http://127.0.0.1:7860/transcribe" -F "file=@audio.mp3"
```

Optional environment variables are documented in `.env.example` (copy to `.env` if needed). No secrets are required for the public Whisper model.

## Test

Install dev dependencies and run unit tests (model loading is skipped; the ASR pipeline is mocked):

```bash
pip install -r requirements-dev.txt
pytest -v
```

## Debug

**VS Code / Cursor:** Open the workspace and use **Run and Debug → FastAPI: Uvicorn** (`.vscode/launch.json`). Set breakpoints in `app.py`; the server runs with `--reload`.

**Manual:** Run uvicorn with `PYTHONUNBUFFERED=1` and attach a debugger to the process, or use `python -m debugpy --listen 5678 -m uvicorn app:app --host 127.0.0.1 --port 7860`.

**Common issues:**

| Symptom | Likely cause |
|--------|----------------|
| `503 Whisper model is not loaded` | Startup still downloading/loading the model, or lifespan failed |
| Slow first request | Normal on CPU; large-v3 is heavy |
| Out of memory | Use a machine with more RAM or a smaller Whisper model |
| `Failed to load Whisper model` | Network/HF Hub issue, or disk full in cache dir |

## Deploy

This repo is configured as a **Hugging Face Space** (Docker SDK). Remote:

`https://huggingface.co/spaces/bajajlakshit/whisper`

**Hugging Face Spaces (recommended):**

1. Push to the Space repo (`git push origin main`).
2. HF builds the `Dockerfile` and exposes port **7860**.
3. No env vars are required for the public model; set `HF_TOKEN` in Space settings only if you switch to a gated model.

**Docker (self-hosted):**

```bash
docker build -t whisper-service .
docker run --rm -p 7860:7860 whisper-service
```

**Environment variables (optional):**

| Variable | Purpose |
|----------|---------|
| `HF_TOKEN` | Hugging Face API token for gated models or higher rate limits |
| `HF_HOME` / `TRANSFORMERS_CACHE` | Override model cache location |

There is no separate CI workflow in this repo; validation is local (`pytest`) and HF Space build logs after push.

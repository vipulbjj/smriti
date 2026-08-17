---
title: Voice Cloning
emoji: 🎙️
colorFrom: purple
colorTo: blue
sdk: docker
app_port: 7860
---

# Voice Cloning API

A FastAPI service for zero-shot voice cloning and speech synthesis using Coqui XTTS-v2.

## Endpoints

- `GET /` — Web UI for uploading voice samples and cloning
- `GET /health` — Health check
- `POST /upload-and-clone` — Upload voice files and create a voice profile
- `POST /clone` — Create a voice profile from at least five voice-note URLs
- `POST /speak` — Synthesize speech from text using a cloned voice (falls back to gTTS if no profile exists)

## Usage

**Clone a voice profile:**

```json
POST /clone
{
  "voice_note_urls": ["https://example.com/note1.mp3", "..."],
  "grandparent_id": "grandma-001"
}
```

**Generate speech:**

```json
POST /speak
{
  "text": "Hello, how are you?",
  "grandparent_id": "grandma-001",
  "language": "hi"
}
```

Returns an MP3 audio file.

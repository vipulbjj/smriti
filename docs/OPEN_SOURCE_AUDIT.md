# smriti — Open-Source & API-Key Audit

Policy (per founder, 2026-05-26): **prefer open-source software over paid services
where quality is comparable, and prefer options that don't require API keys.**

This audit covers every external dependency across Smriti and its vertical repos,
the choice made, and what's genuinely unavoidable.

| Capability | Was / paid option | Chosen open-source / keyless option | Key needed? | Notes |
|---|---|---|---|---|
| **Video assembly** (smriti-reel) | Shotstack (paid, per-render) | **ffmpeg** local render (`assembler.py`) | ❌ none | ffmpeg is now the default. Shotstack kept only as a hosted fallback for keyless-but-ffmpeg-less hosts. |
| **Voice cloning** (smriti-voice) | ElevenLabs (paid) | **Coqui XTTS-v2** (MPL-2.0) | ❌ none | Model is open weights; needs a GPU, not a key. |
| **TTS fallback** | ElevenLabs (paid) | **gTTS** | ❌ none | Already keyless. |
| **Transcription** (smriti-whisper) | Groq hosted (free tier, key) | **faster-whisper / whisper-large-v3** local | ❌ none (local) | `WHISPER_BACKEND=local` runs open weights on a GPU, no key, no rate limit. Groq stays as a no-GPU convenience default. |
| **Photo restoration** (photo_story) | Replicate (paid per-second) | **GFPGAN · Real-ESRGAN · DeOldify** (open weights) | ⚠️ key if hosted on Replicate | Models are open-source; Replicate is just a paid host. Keyless path = self-host on a GPU (Modal free tier / HF Space) — the intern-plan design. Provider-agnostic already. |
| **Vision / story seed** (photo_story) | OpenAI (paid) | **Llama-3.2-Vision via Groq** (free tier) | ⚠️ key (free) | Open *weights* (Llama), so no lock-in; can self-host the same model to drop the key. |
| **Illustration** (smriti-reel) | — | **SDXL / Flux** | ⚠️ key (HF free tier) | Open weights. Keyless path = local SDXL on a GPU. For *photo mode* no image gen is needed at all → fully keyless. |
| **Image-prompt LLM** (smriti-reel) | OpenAI | **Llama-3.1 via Groq** (free) | ⚠️ key (free) | Open weights; self-hostable. |
| **WhatsApp transport** | Twilio (paid per msg) | **Meta WhatsApp Cloud API** (free ≤1k convos/mo) | ✅ key (unavoidable) | WhatsApp is a closed platform — there is **no** open-source/keyless way to send WhatsApp messages. Meta is the cheapest legitimate option and is already the chosen default. |
| **Print fulfilment** (vertical #6, not yet built) | — | **Typst** (typesetting, open-source) + Pothi/Lulu (print) | ⚠️ key for print order | Typesetting is fully open-source/keyless; only the physical print-order API needs a key (intrinsic to ordering a real book). |

## Summary

- **Fully open-source & keyless now:** video assembly (ffmpeg), voice cloning (XTTS-v2), local transcription (faster-whisper), TTS fallback (gTTS).
- **Open weights, key only because of a hosted convenience:** photo restoration, vision, illustration, prompt LLM — every one can be self-hosted on a GPU to drop the key, with zero model change. The code is already provider-agnostic.
- **Unavoidable keys:** WhatsApp (closed platform) and physical print ordering. These are intrinsic to the task, not a tooling choice.

## Practical default per environment

- **No GPU (laptop / cheap Vercel):** use the free-tier hosted keys (Groq, HF) + ffmpeg locally. Cheapest to operate today.
- **With a GPU (Modal / HF Space / rented A10):** flip every ⚠️ to ❌ — self-host whisper, restoration, vision, illustration, and XTTS. No per-call cost, no rate limits, no vendor risk on the revenue product. This is the target end-state.

# smriti — Strategy 2026: The Open-Source Memory Engine

*Companion to `DESIGN.md` (the approved YC Office Hours plan). That doc owns the go-to-market wedge (Concierge → WhatsApp → AI Vault). This doc owns the **product and technical direction of the AI layer** — what Phase 3 actually becomes, and why it's built on open models.*

Author: autonomous build session, 2026-05-26
Status: PROPOSAL (not yet validated against paying families)

---

## 1. The reframe: from "memoir service" to "memory engine"

`DESIGN.md` correctly establishes the wedge: an affluent Indian grandchild pays to preserve an aging grandparent's stories. The book and the WhatsApp prompts are the *delivery mechanism*. They are not the product.

**The product is reconstruction.** A family doesn't just want their grandfather's words transcribed. They want:

- His **voice** preserved and usable — even after he's gone ("talk to nanu").
- His **stories** elicited, not just recorded — most elderly people don't volunteer narrative; they answer questions.
- His **photographs** — cracked, faded, black-and-white, water-damaged — brought back to life and, where possible, *moving*.
- All of it **woven into one artifact** the family keeps forever.

This is a *memory reconstruction engine* with a WhatsApp front door. The front door (already built) is the moat against StoryWorth and local videographers. The engine is the moat against the next well-funded copycat.

The two reference products the founder named map cleanly onto two halves of the engine:

| Founder's reference | What it is | smriti's equivalent |
|---|---|---|
| **Wispr Flow** | Frictionless, best-in-class voice → text | **Capture**: elderly-friendly voice as the *primary* input. Zero typing. Transcription so good it preserves dialect and emotion. |
| **Kling** | Image/text → video | **Reconstruction**: still photos → restored → colorized → *animated*. The dead photo breathes. |

The new capability that sits *between* them — and that no competitor has — is **story-from-image**: hand smriti a damaged 1962 photograph and it (a) restores it, (b) reads it, and (c) generates the questions that pull the real story out of the grandparent, then narrates the result in their own voice.

---

## 2. Why open-source models (and where we deliberately don't)

The founder's instruction: build it "the open-source way." This is not ideology — it is unit economics and defensibility.

### The cost problem with the current stack

Phase 3 as scoped in `DESIGN.md` leans on proprietary APIs:

- **ElevenLabs** voice cloning — ~$22–99/mo + per-character; voice clone quality is excellent but cost scales with every "talk to grandpa" interaction.
- **Shotstack** video — currently watermarked sandbox; prod is paid per render.
- **D-ID / RunwayML** photo animation — expensive per-clip, usage-metered.
- **OpenAI** — per-token, per-image.

At ₹50k–₹1.5L per AI Vault package with heavy per-family compute (15 min voice clone, 5–10 animated clips, full transcription), proprietary per-call pricing erodes margin and caps how generous each package can be. Worse: every one of these is a dependency that can change pricing or terms overnight on the *primary revenue product*.

### The open-source pipeline

Every stage has a credible open model. We can run them via a GPU host (Replicate / Modal / Fal / a rented A10) and pay for compute, not per-call rent:

| Stage | Proprietary (current) | Open-source replacement | Notes |
|---|---|---|---|
| Transcription | (already Groq Whisper) | **whisper-large-v3** (open weights) | Already open; Groq just hosts it cheaply. Keep. |
| Face restoration | — | **GFPGAN**, **CodeFormer** | Repairs blurred/damaged faces in old photos. |
| Upscale / denoise | — | **Real-ESRGAN**, **SwinIR** | Detail recovery on low-res scans. |
| Colorization | — | **DeOldify**, **DDColor** | B&W → color, the emotional money-shot. |
| Photo animation | D-ID / Runway / Kling | **LivePortrait** (face), **CogVideoX / LTX-Video / Mochi** (scene) | The "Kling alternative." LivePortrait animates a face from a driving video; CogVideoX does image→video. |
| Voice clone / TTS | ElevenLabs | **XTTS-v2 (Coqui)**, **F5-TTS**, **OpenVoice** | Hindi/Punjabi support is the open risk — must blind-test (see §5). |
| Story/vision reasoning | OpenAI | **Llama-3.2-Vision** (via Groq, free tier today) | Vision reasoning to "read" a photo and draft prompts. |

**Where we deliberately stay proprietary (for now):** the *vision + language reasoning* runs on Groq's hosted Llama, because it's free today, fast, and already wired into `ai.py`. It's open-weights underneath, so we're not locked in — we can self-host the same model later. This is the pragmatic line: open *weights* everywhere (no lock-in), self-host only where the per-call economics justify the ops burden.

### The strategic payoff

1. **Margin**: compute-priced, not rent-priced. A family's whole AI Vault can be generated for the cost of GPU-minutes, not a stack of metered API bills.
2. **No vendor risk** on the revenue product.
3. **A genuine open-source story** — which, for a founder building in public (the `launch-thread` / `announce` skills exist for a reason), is its own distribution channel. "We rebuilt the entire memory-reconstruction pipeline on open models so families own their memories, not a SaaS vendor" is a *thread that writes itself*.

---

## 3. The flagship new feature: story-from-image

This is the wedge inside the wedge — the thing to build first because it's the most distinctive and the most emotionally undeniable.

### User flow

1. Grandchild or grandparent sends an **old photo** over WhatsApp (already supported — `Story.photo_data` exists).
2. smriti **restores** it: face repair (GFPGAN) → upscale (Real-ESRGAN) → colorize (DeOldify). Result stored alongside the original (never destroys the original).
3. smriti **reads** it with a vision model and generates two things:
   - A short, evocative **story seed** in the grandparent's language ("A young couple stands in front of a Fiat, the woman in a cotton sari, monsoon clouds behind them…").
   - **3–4 warm, specific elicitation questions** sent back to the grandparent to pull the *real* story ("Is this your wedding car? Who is standing on the left? Where was this taken?").
4. The grandparent's reply (voice, naturally) becomes the **true caption**. The AI seed is scaffolding, never the final word — *we never fabricate family history*.
5. Restored photo + true story + (optionally) narration in their cloned voice + a LivePortrait animation = one timeline entry and one page in the book.

### The hard ethical line (non-negotiable, see `CLAUDE.md` voice rules)

The AI **never invents family facts**. It describes what is *visually present* and asks questions. The narrative in the final artifact comes from the human. This is both an ethics rule and a product rule: a fabricated memory is worse than no memory, and for a grief-adjacent product it would be catastrophic to trust. The generated story seed is always clearly an *editor's prompt*, never presented to the family as fact.

### Why this first

- It reuses everything already built (WhatsApp media intake, the cron pipeline, the Story model, the timeline, the book).
- It is **demonstrable in a single WhatsApp exchange** — the perfect thing to show the founder's sister, or to put in a launch thread.
- The restored-photo before/after is the single most shareable artifact the product can produce. It *is* the growth engine `DESIGN.md` asks for (the 60-second shareable clip).

---

## 4. Monetization (refresh of the DESIGN.md pricing)

`DESIGN.md`'s tiers stand. This layer makes the AI Vault deliverable *and* opens two new revenue surfaces the open-source engine unlocks:

### Existing tiers (unchanged)
- Concierge ₹25k · WhatsApp memoir ₹15k/yr · AI Vault ₹50k–₹1.5L.

### New: à la carte "Revive" (lowers the entry price, feeds the funnel)
- **Photo Revival**: send up to 10 old photos, get them restored + colorized + (optionally) one animated clip. **₹2,500–₹5,000.** No subscription. This is the *trial drug* — a grandchild who would balk at ₹50k will pay ₹3k to see their grandmother's wedding photo in color, and that artifact sells the full Vault.
- It also has standalone viral potential well beyond the memoir buyer — anyone with a dead relative's photo is a customer for a one-shot ₹3k revival.

### New: the engine as the asset
Once the open pipeline is solid, the **reconstruction engine itself** is licensable: regional photo studios, genealogy services, even funeral homes could white-label "restore + animate + narrate." This is a Phase 4 thought, noted so the architecture is built provider-agnostic from day one (it is — see §6).

### Margin logic
The à la carte tier only works if per-photo cost is GPU-minutes, not metered API rent. **This is the concrete reason the open-source path is a monetization decision, not an engineering preference.** A ₹3,000 Photo Revival at proprietary per-call pricing might cost ₹1,200 in API fees; on self-hosted open models it's closer to ₹150 in compute. The first makes the funnel uneconomic; the second makes it a loss-leader you can run all day.

---

## 5. Risks and the empirical tests that retire them

| Risk | Test before betting on it |
|---|---|
| **Open TTS can't do natural Hindi/Punjabi** (highest risk) | Blind A/B: XTTS-v2 / F5-TTS vs ElevenLabs on a 5-min Hindi sample, judged by 3 native speakers. `DESIGN.md` already mandates this bar. If open fails, keep ElevenLabs for voice *only* and run everything else open. |
| **Restoration looks "AI-fake"** (uncanny, over-smoothed faces) | Show 10 families before/after pairs. If they react with "that's not really him," tune toward conservative restoration (CodeFormer fidelity weight high). A subtle real-looking repair beats a dramatic plastic one. |
| **Animation is creepy** (the "living photo of the dead" can disturb) | This is an emotional, not technical, test. Offer animation as opt-in, never default. Some families will love it; some will find it haunting. Let them choose. |
| **Photo-story fabrication erodes trust** | Enforced in code: vision model is prompted to describe-and-ask only. Never ship a generated narrative as fact. (§3) |
| **GPU ops burden** on a solo founder | Start on Replicate/Fal (pay-per-second, zero ops). Only self-host when volume makes a rented A10 cheaper. Don't prematurely run your own GPUs. |

---

## 6. Technical architecture (as built this session)

The pipeline is implemented **provider-agnostic** so the open/proprietary line can move without touching call sites:

```
WhatsApp photo  ──►  Story.photo_data (raw, never mutated)
                          │
            cron /process-pending  (existing 15-min loop)
                          │
                ┌─────────┴───────────┐
                ▼                     ▼
        photo_story.describe_   photo_story.restore_photo()
        and_story()             (GFPGAN→ESRGAN→DeOldify via
        (Groq Llama-Vision,     Replicate; None if no token)
         free tier)                   │
                │                     ▼
                ▼              Story.restored_photo_data
        Story.photo_description        Story.colorized_photo_data
        Story.photo_story_text
                │
                ▼
        elicitation questions ──► WhatsApp back to grandparent
```

**Design rules honored:**
- Every provider returns `None` when its key is absent (matches `ai.py` / `video.py` / `tts.py` convention) — the feature degrades silently, never crashes the webhook.
- The **original photo is never overwritten**. Restoration writes to *new* columns.
- Heavy work runs in the **cron pipeline**, not the webhook (Vercel timeout safety — same pattern as text enhancement).
- New config: `REPLICATE_API_TOKEN`. Absent → restoration skipped, vision-story still runs on free Groq.

**Schema note (action required before prod):** four additive columns on `Story`. `create_all()` adds them on a fresh DB but **not** on the existing prod DB — this is exactly the Alembic gap flagged in `TODOS.md` (P1). Set up the Alembic baseline before this ships to a live family.

---

## 7. What was NOT done this session (honest scope)

This session delivered: the strategy (this doc), the **story-from-image pipeline** (vision description + story seed + restoration scaffold, tested), and the wiring into the existing cron loop. Deliberately **not** done, because each is a real project needing its own validation:

- Voice cloning swap (ElevenLabs → open) — gated on the blind-test in §5.
- Photo *animation* (LivePortrait / CogVideoX) — scaffolded interface only; the actual model wiring is a follow-up.
- The à la carte "Photo Revival" purchase flow — a monetization decision to make with real pricing data.
- Anything deployed. No commits, no pushes. All changes are local and reviewable.

The single most important next action remains the one `DESIGN.md` ends on: **a paying conversation.** No amount of pipeline replaces it.

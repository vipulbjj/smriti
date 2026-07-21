"""
Story-from-image pipeline — the smriti reconstruction engine.

Given an old family photograph, this module:

  1. restore_photo()    — face repair + upscale via open models (GFPGAN, Real-ESRGAN)
  2. colorize_photo()   — black-and-white → color via DeOldify
  3. describe_and_story()— a vision model reads the photo and returns:
       • a factual description of what is *visually present*
       • a short evocative story SEED (scaffolding, never presented as fact)
       • 3-4 warm elicitation questions to pull the real story from the grandparent

Hard rule (see docs/STRATEGY_2026.md §3): the AI never invents family history.
It describes what it sees and asks questions. The true story always comes from
the human. The story seed is an editor's prompt, not a memory.

Provider policy (matches ai.py / video.py / tts.py):
  • Every function returns None when its provider key is absent.
  • Restoration (Replicate) is optional — absent token → restoration skipped,
    the vision story-seed still runs on Groq's free tier.
"""

import base64
import json
import logging
from dataclasses import dataclass, field
from typing import Optional

from .config import config

logger = logging.getLogger(__name__)

# Open-source models hosted on Replicate. Pinned versions are set via env so the
# pipeline can be upgraded without a code change.
_GFPGAN = "tencentarc/gfpgan"
_DEOLDIFY = "arielreplicate/deoldify_image"

_MIN_DESCRIPTION_CHARS = 10


@dataclass
class PhotoStoryResult:
    """Output of describe_and_story(). All fields are scaffolding, never fact."""
    description: str                      # what is visually present
    story_seed: str                       # evocative seed in the grandparent's language
    questions: list[str] = field(default_factory=list)  # elicitation questions

    def questions_message(self, name: str, language: str = "english") -> str:
        """Format the elicitation questions as a WhatsApp message to the grandparent."""
        intro = _QUESTION_INTRO.get(language, _QUESTION_INTRO["english"]).format(name=name)
        bullets = "\n".join(f"• {q}" for q in self.questions)
        return f"{intro}\n\n{bullets}"


_QUESTION_INTRO = {
    "hindi": "📷 {name} जी, यह तस्वीर देखकर कुछ सवाल मन में आए — जो याद हो, बताइए:",
    "english": "📷 {name}, this photo brought a few questions to mind — share whatever you remember:",
    "punjabi": "📷 {name} ਜੀ, ਇਹ ਤਸਵੀਰ ਵੇਖ ਕੇ ਕੁਝ ਸਵਾਲ ਮਨ ਵਿੱਚ ਆਏ — ਜੋ ਯਾਦ ਹੋਵੇ, ਦੱਸੋ:",
}

_LANG_NAME = {"hindi": "Hindi", "english": "English", "punjabi": "Punjabi"}

_VISION_SYSTEM = (
    "You are a sensitive archival assistant for a family-memory product. You are shown an "
    "OLD family photograph. Your job has strict rules:\n"
    "1. DESCRIBE only what is visually present — people, clothing, setting, era cues, objects, "
    "mood. Never guess names, relationships, dates, or events. If unsure, say so.\n"
    "2. Write a short, warm STORY SEED (2-3 sentences) that evokes the scene. This is a writer's "
    "prompt to spark memory, NOT a claim about what happened. Never state family facts as true.\n"
    "3. Propose 3-4 specific, gentle QUESTIONS that would help the elderly person in the family "
    "tell the real story behind this photo.\n"
    "Return STRICT JSON: {{\"description\": str, \"story_seed\": str, \"questions\": [str, ...]}}. "
    "Write story_seed and questions in {lang}. No prose outside the JSON."
)


def _get_groq():
    from groq import Groq
    return Groq(api_key=config.groq_api_key)


def _data_url(photo_bytes: bytes, content_type: str = "image/jpeg") -> str:
    b64 = base64.b64encode(photo_bytes).decode("ascii")
    return f"data:{content_type};base64,{b64}"


def describe_and_story(
    photo_bytes: bytes,
    grandparent_name: str,
    language: str = "english",
    prompt_text: str = "",
) -> Optional[PhotoStoryResult]:
    """Read a photo with a vision model. Returns scaffolding to elicit the real story.

    Returns None if Groq is unavailable or the model output can't be parsed.
    """
    if not config.groq_api_key:
        return None
    if not photo_bytes:
        return None

    try:
        client = _get_groq()
        system = _VISION_SYSTEM.format(lang=_LANG_NAME.get(language, "English"))
        user_text = "Describe this family photograph and help the family tell its story."
        if prompt_text:
            user_text += f" Context — today's memory prompt was: {prompt_text}"

        resp = client.chat.completions.create(
            model=config.vision_model,
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image_url", "image_url": {"url": _data_url(photo_bytes)}},
                    ],
                },
            ],
            max_tokens=700,
            temperature=0.6,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content.strip()
        data = json.loads(raw)
    except Exception:
        logger.exception("Vision story generation failed for %s", grandparent_name)
        return None

    description = (data.get("description") or "").strip()
    story_seed = (data.get("story_seed") or "").strip()
    questions = [q.strip() for q in (data.get("questions") or []) if q and q.strip()]

    if len(description) < _MIN_DESCRIPTION_CHARS:
        logger.warning("Vision description too short for %s — discarding", grandparent_name)
        return None

    return PhotoStoryResult(description=description, story_seed=story_seed, questions=questions)


def _get_replicate():
    import replicate
    return replicate.Client(api_token=config.replicate_api_token)


def _run_replicate_image(model: str, photo_bytes: bytes, input_key: str = "img",
                         extra: Optional[dict] = None) -> Optional[bytes]:
    """Run an open image model on Replicate and download the result bytes.

    Returns None if Replicate isn't configured or the run fails. Replicate returns
    a URL (or list of URLs); we fetch the bytes so they can be stored permanently.
    """
    if not config.replicate_api_token:
        return None
    try:
        import httpx

        client = _get_replicate()
        payload = {input_key: _data_url(photo_bytes)}
        if extra:
            payload.update(extra)
        output = client.run(model, input=payload)

        url = output[0] if isinstance(output, (list, tuple)) else output
        url = str(url)
        resp = httpx.get(url, timeout=60)
        resp.raise_for_status()
        return resp.content
    except Exception:
        logger.exception("Replicate model %s failed", model)
        return None


def restore_photo(photo_bytes: bytes) -> Optional[bytes]:
    """Face repair + upscale on a damaged/blurred old photo (GFPGAN).

    Returns restored image bytes, or None if Replicate isn't configured / fails.
    Conservative by default (version=v1.4, scale=2) to avoid an over-smoothed,
    'AI-fake' look — see STRATEGY_2026.md §5.
    """
    if not photo_bytes:
        return None
    return _run_replicate_image(
        _GFPGAN,
        photo_bytes,
        input_key="img",
        extra={"version": "v1.4", "scale": 2},
    )


def colorize_photo(photo_bytes: bytes) -> Optional[bytes]:
    """Colorize a black-and-white photo (DeOldify).

    Returns colorized image bytes, or None if Replicate isn't configured / fails.
    """
    if not photo_bytes:
        return None
    return _run_replicate_image(
        _DEOLDIFY,
        photo_bytes,
        input_key="input_image",
        extra={"render_factor": 35},
    )


def reconstruct_photo(photo_bytes: bytes) -> tuple[Optional[bytes], Optional[bytes]]:
    """Full restoration pass: returns (restored_bytes, colorized_bytes).

    Colorization runs on the restored output when available, so the final color
    image benefits from the face repair + upscale first. Each stage degrades
    independently to None.
    """
    restored = restore_photo(photo_bytes)
    base = restored if restored else photo_bytes
    colorized = colorize_photo(base)
    return restored, colorized

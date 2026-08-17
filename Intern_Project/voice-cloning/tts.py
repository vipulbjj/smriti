import asyncio
import logging
from pathlib import Path

from gtts import gTTS

from voice import synthesize_speech


logger = logging.getLogger(__name__)


async def speak(
    text: str,
    output_path: str,
    voice_model_path: str | None = None,
    language: str = "hi",
) -> str:
    """Generate speech with a cloned voice when available, otherwise gTTS."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if voice_model_path:
        model_dir = Path(voice_model_path)
        manifest_path = model_dir / "voice_profile.txt"

        # Prefer the cloned grandparent voice only when the profile folder and
        # manifest are present. If cloned synthesis fails, log it and fall back
        # to gTTS so the caller still receives an audio file.
        if model_dir.exists() and model_dir.is_dir() and manifest_path.exists():
            try:
                await synthesize_speech(
                    text=text,
                    model_path=str(model_dir),
                    output_path=output_path,
                    language=language,
                )
                return output_path
            except Exception as exc:
                logger.warning(
                    "Cloned voice synthesis failed; falling back to gTTS: %s",
                    exc,
                )

    def save_with_gtts() -> None:
        # gTTS performs network and file I/O, so run it off the async event loop.
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(output_path)

    # Fallback path: use standard gTTS when no valid cloned profile is available
    # or when cloned synthesis fails at runtime.
    await asyncio.to_thread(save_with_gtts)
    return output_path

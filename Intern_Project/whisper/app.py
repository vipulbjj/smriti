import logging
import os
import re
import shutil
import subprocess
import tempfile
import wave
from contextlib import asynccontextmanager
from typing import Any

import torch
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from transformers import __version__ as transformers_version
from transformers import pipeline
from transformers.models.whisper.tokenization_whisper import TO_LANGUAGE_CODE

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Global runtime objects are initialized once during application startup.
MODEL_ID = "openai/whisper-large-v3"
device: str = "cuda" if torch.cuda.is_available() else "cpu"
asr_pipeline: Any | None = None

GROQ_MODEL = "llama3-8b-8192"
GROQ_SYSTEM_PROMPT = """You are helping preserve stories of elderly Indian grandparents. Clean up this transcript that was recorded by a grandparent who may stammer, self-correct, or mix Hindi, English, and Punjabi.

Rules:
1. Remove stammering (e.g. 'mai mai mai gaya' → 'mai gaya', 'I I I was' → 'I was')
2. SELF CORRECTION RULES (highest priority rule): A self-correction happens when a speaker realizes they said something wrong and corrects it.
   STEP 1 - Detect correction signals: English: sorry, no, not, I mean, actually, wait, correction, rather, instead, what I meant. Hindi: nahi, nahi nahi, matlab, seedha bolunga, galat bola, sahi baat. Mixed: sorry nahi, no no matlab.
   STEP 2 - Identify the pattern: Pattern A: [wrong info] + [signal] + [correct info] → keep correct. Pattern B: [signal] + [wrong info] + [correct info] → keep correct. Pattern C: [wrong info] + not + [wrong info] + [correct info] → keep correct. Pattern D: Partial correction e.g. 'we went to Delhi... actually Agra' → Agra.
   STEP 3 - Apply the correction: Remove wrong information completely; remove correction signal words; keep ONLY final correct information; reconstruct sentence naturally.
   STEP 4 - Handle multiple corrections: Last correction wins — 'X... no Y... wait actually Z' → Z.
   IMPORTANT: Never keep both wrong and right information; last thing they say is the truth; apply to names, places, dates, facts; works for any language or mix; when in doubt, keep the later statement.
   Example: 'his name was Lakshmi no no his name was Shivam' → 'his name was Shivam'
3. Remove Hindi fillers: acha, haan, matlab, arrey, bas, toh, waise. Keep English fillers um, uh only if they were in the original transcript
4. Keep idioms exactly as spoken — never translate or change idioms
5. Convert spoken Hindi dates to numbers (e.g. 'unnees sau saath' → '1967', 'pachaas ka daur' → 'the 1950s')
6. Keep the mix of Hindi, English, and Punjabi exactly as spoken — do not translate or homogenize
7. Keep the meaning exactly as intended
8. Preserve the grandparent's natural voice and style — do not make it formal
9. Fix obvious speech errors but keep personality intact
10. If they repeat a story or correct themselves, use the final corrected version only — never keep both the wrong and corrected versions

Return only the cleaned transcript, nothing else."""

# Transformers 4.46+ Whisper long-form thresholds (OpenAI-whisper style).
# condition_on_previous_text is not a Transformers kwarg — do not pass it.
WHISPER_GENERATE_KWARGS = {
    "compression_ratio_threshold": 2.4,
    "logprob_threshold": -1.0,
    "no_speech_threshold": 0.6,
}
WHISPER_LONG_FORM_TEMPERATURES = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]


def resolve_ffmpeg_path() -> str | None:
    """Return ffmpeg executable path from PATH or imageio-ffmpeg bundle."""
    path = shutil.which("ffmpeg")
    if path:
        return path
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


# Suffixes that usually need ffmpeg conversion before Whisper reads them as WAV.
CONVERTIBLE_AUDIO_SUFFIXES = frozenset(
    {".webm", ".ogg", ".opus", ".oga", ".m4a", ".mp4", ".aac", ".weba"}
)

# ffmpeg input strategies tried in order (empty list = auto-detect container).
FFMPEG_INPUT_FORMAT_ATTEMPTS: list[list[str]] = [
    [],
    ["-f", "webm"],
    ["-f", "ogg"],
]


def suffix_from_upload(filename: str | None, content_type: str | None) -> str:
    """Pick a stable file suffix from filename or MIME type."""
    if filename:
        ext = os.path.splitext(filename)[1].lower()
        if ext:
            return ext

    mime_to_suffix = {
        "audio/webm": ".webm",
        "audio/ogg": ".ogg",
        "audio/opus": ".opus",
        "audio/mp4": ".m4a",
        "audio/m4a": ".m4a",
        "audio/mpeg": ".mp3",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/flac": ".flac",
    }
    if content_type:
        base = content_type.split(";", 1)[0].strip().lower()
        return mime_to_suffix.get(base, "")
    return ""


def needs_audio_conversion(suffix: str, content_type: str | None) -> bool:
    """Whether we should attempt ffmpeg conversion before Whisper."""
    if suffix.lower() in CONVERTIBLE_AUDIO_SUFFIXES:
        return True
    if content_type:
        base = content_type.split(";", 1)[0].strip().lower()
        if base in ("audio/webm", "audio/ogg", "audio/opus", "audio/mp4", "audio/m4a"):
            return True
    return False


def write_upload_to_temp(contents: bytes, suffix: str) -> str:
    """Write upload bytes to a temp file and ensure they are flushed to disk."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(contents)
        temp_file.flush()
        os.fsync(temp_file.fileno())
        return temp_file.name


def convert_to_wav_with_ffmpeg(
    ffmpeg: str,
    input_path: str,
    wav_path: str,
) -> tuple[bool, str]:
    """
    Try several ffmpeg input-format strategies. Returns (success, last_stderr).
    """
    last_stderr = ""
    for format_args in FFMPEG_INPUT_FORMAT_ATTEMPTS:
        cmd = [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            *format_args,
            "-i",
            input_path,
            "-ar",
            "16000",
            "-ac",
            "1",
            "-y",
            wav_path,
        ]
        proc = subprocess.run(cmd, capture_output=True, check=False)
        if proc.returncode == 0 and os.path.isfile(wav_path) and os.path.getsize(wav_path) > 0:
            return True, ""
        last_stderr = (proc.stderr or b"").decode(errors="replace").strip()

    return False, last_stderr or "ffmpeg could not convert audio to WAV"


def transcription_error_response(status_code: int, error: str, message: str) -> JSONResponse:
    """Return a consistent JSON error body for /transcribe failures."""
    return JSONResponse(
        status_code=status_code,
        content={"error": error, "message": message},
    )


def audio_duration_seconds(path: str) -> float:
    """Best-effort audio duration for choosing Whisper generation settings."""
    try:
        with wave.open(path, "rb") as wf:
            rate = wf.getframerate()
            if rate > 0:
                return wf.getnframes() / float(rate)
    except wave.Error:
        pass

    ffmpeg = resolve_ffmpeg_path()
    if not ffmpeg:
        return 0.0

    try:
        proc = subprocess.run(
            [ffmpeg, "-hide_banner", "-i", path],
            capture_output=True,
            text=True,
            check=False,
        )
        for line in (proc.stderr or "").splitlines():
            if "Duration:" in line:
                duration_token = line.split("Duration:", 1)[1].split(",")[0].strip()
                hours, minutes, seconds = duration_token.split(":")
                return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    except Exception:
        pass

    return 0.0


def build_whisper_generate_kwargs(audio_path: str) -> dict[str, Any]:
    """
    Build generate kwargs compatible with Transformers 4.46.3.

    Short clips (<=30s) require a float temperature when thresholds are set.
    Long clips need a temperature list to activate threshold fallback.
    """
    kwargs = dict(WHISPER_GENERATE_KWARGS)
    if audio_duration_seconds(audio_path) > 30:
        kwargs["temperature"] = WHISPER_LONG_FORM_TEMPERATURES
    else:
        kwargs["temperature"] = 0.0
    return kwargs


def resolve_whisper_language(language: str | None) -> str | None:
    """Map optional ISO/name input to a Whisper generate_kwargs language name."""
    if not language or not language.strip():
        return None
    lang = language.strip().lower()
    for name, code in TO_LANGUAGE_CODE.items():
        if lang == code or lang == name:
            return name
    return lang


def is_whisper_urdu(language: str | None) -> bool:
    """True if Whisper detected Urdu (ur, urdu, etc. via TO_LANGUAGE_CODE)."""
    if not language:
        return False
    lang = language.strip().lower()
    code = TO_LANGUAGE_CODE.get(lang, lang)
    return code == "ur" or lang == "urdu"


def parse_whisper_result(result: Any) -> tuple[str, str | None]:
    """Extract transcript text and normalized language code from a pipeline result."""
    text = result.get("text", "") if isinstance(result, dict) else ""
    whisper_language = result.get("language") if isinstance(result, dict) else None
    if whisper_language is None and isinstance(result, dict):
        chunks = result.get("chunks") or []
        if chunks:
            whisper_language = chunks[0].get("language")
    if whisper_language:
        whisper_language = TO_LANGUAGE_CODE.get(whisper_language, whisper_language)
    return text, whisper_language


# Romanized Hindi/Hinglish cues (Latin script).
HINGLISH_WORDS = frozenset(
    {
        "acha",
        "achha",
        "haan",
        "han",
        "nahi",
        "nahin",
        "hai",
        "hain",
        "main",
        "mein",
        "tum",
        "aap",
        "kya",
        "kyun",
        "kyon",
        "matlab",
        "waise",
        "bahut",
        "bohot",
        "thoda",
        "kabhi",
        "jab",
        "tab",
        "yeh",
        "ye",
        "woh",
        "wo",
        "kuch",
        "sab",
        "aur",
        "lekin",
        "par",
        "phir",
        "fir",
        "bhi",
        "ji",
        "beta",
        "beti",
        "dada",
        "dadi",
        "nana",
        "nani",
    }
)

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
GURMUKHI_RE = re.compile(r"[\u0A00-\u0A7F]")
LATIN_RE = re.compile(r"[a-zA-Z]")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load Whisper on startup and release it on shutdown."""
    global asr_pipeline

    ffmpeg_path = resolve_ffmpeg_path()
    logger.info(
        "Startup: torch=%s transformers=%s device=%s ffmpeg=%s",
        torch.__version__,
        transformers_version,
        device,
        ffmpeg_path or "(not found)",
    )

    try:
        torch_dtype = torch.float16 if device == "cuda" else torch.float32

        # The Transformers pipeline handles preprocessing, generation, and decoding.
        asr_pipeline = pipeline(
            task="automatic-speech-recognition",
            model=MODEL_ID,
            torch_dtype=torch_dtype,
            device=0 if device == "cuda" else -1,
        )
        logger.info("Whisper model loaded: %s", MODEL_ID)
    except Exception as exc:
        logger.exception("Failed to load Whisper model")
        raise RuntimeError(f"Failed to load Whisper model: {exc}") from exc

    yield

    # Clear the global pipeline reference when the application shuts down.
    asr_pipeline = None


# Create the FastAPI application instance with lifespan startup/shutdown handling.
app = FastAPI(title="Self-hosted Whisper Transcription Service", lifespan=lifespan)


def detect_mixed_language(text: str, whisper_language: str | None) -> str:
    """Classify transcript language for elderly Indian speech."""
    has_devanagari = bool(DEVANAGARI_RE.search(text))
    has_gurmukhi = bool(GURMUKHI_RE.search(text))
    has_latin = bool(LATIN_RE.search(text))

    if has_gurmukhi:
        return "pa"

    if has_devanagari and has_latin:
        return "hi-en"

    if has_devanagari:
        return "hi"

    if has_latin:
        words = {w.lower() for w in re.findall(r"[a-zA-Z]+", text)}
        if words & HINGLISH_WORDS:
            return "hi-en"
        return "en"

    if whisper_language:
        code = TO_LANGUAGE_CODE.get(whisper_language, whisper_language)
        if code in ("hi", "hin"):
            return "hi"
        if code in ("pa", "pan"):
            return "pa"
        if code in ("en", "eng"):
            return "en"

    return "hi-en"


def cleanup_transcript_with_groq(raw_transcript: str) -> tuple[str, bool]:
    """
    Post-process Whisper output via Groq. Returns (transcript, corrections_made).
    Never raises; falls back to raw transcript on any failure.
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return raw_transcript, False

    try:
        from groq import Groq

        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": GROQ_SYSTEM_PROMPT},
                {"role": "user", "content": raw_transcript},
            ],
            temperature=0.2,
        )
        cleaned = (response.choices[0].message.content or "").strip()
        if not cleaned:
            return raw_transcript, False
        return cleaned, True
    except Exception as exc:
        logger.warning("Groq transcript cleanup failed, using raw Whisper output: %s", exc)
        return raw_transcript, False


@app.get("/")
async def root():
    return FileResponse("/app/index.html")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Return a simple health check response."""
    return {"status": "ok"}


@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str | None = Query(
        default=None,
        description='Optional Whisper language hint (e.g. "hi" or "hindi"). Omitted = auto-detect.',
    ),
) -> dict[str, str | bool | None]:
    """Accept an uploaded audio file, transcribe it, and return the text."""
    if asr_pipeline is None:
        raise HTTPException(
            status_code=503,
            detail={"error": "model_unavailable", "message": "Whisper model is not loaded"},
        )

    temp_file_path: str | None = None
    wav_path: str | None = None

    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(
                status_code=400,
                detail={"error": "empty_file", "message": "Uploaded audio file is empty"},
            )

        suffix = suffix_from_upload(file.filename, file.content_type)
        temp_file_path = write_upload_to_temp(contents, suffix)

        transcription_path = temp_file_path
        if needs_audio_conversion(suffix, file.content_type):
            ffmpeg = resolve_ffmpeg_path()
            if ffmpeg:
                base, _ = os.path.splitext(temp_file_path)
                wav_path = base + ".wav"
                ok, stderr = convert_to_wav_with_ffmpeg(ffmpeg, temp_file_path, wav_path)
                if ok:
                    transcription_path = wav_path
                else:
                    logger.warning(
                        "ffmpeg conversion failed for %s (%s); falling back to original upload: %s",
                        file.filename,
                        suffix or file.content_type,
                        stderr,
                    )
            else:
                logger.warning(
                    "ffmpeg not found; attempting Whisper on original upload (%s)",
                    suffix or file.content_type,
                )

        # Run Whisper inference with settings tuned for elderly speech.
        generate_kwargs = build_whisper_generate_kwargs(transcription_path)
        generate_kwargs["task"] = "transcribe"
        resolved_language = resolve_whisper_language(language)
        if resolved_language is not None:
            generate_kwargs["language"] = resolved_language
        result = asr_pipeline(
            transcription_path,
            return_language=True,
            generate_kwargs=generate_kwargs,
        )

        raw_transcript, whisper_language = parse_whisper_result(result)

        # English/Hindi/Urdu only: Urdu → forced Hindi re-transcription.
        if is_whisper_urdu(whisper_language):
            retranscribe_kwargs = build_whisper_generate_kwargs(transcription_path)
            retranscribe_kwargs.update(
                {
                    "language": "hindi",
                    "task": "transcribe",
                }
            )
            result = asr_pipeline(
                transcription_path,
                return_language=True,
                generate_kwargs=retranscribe_kwargs,
            )
            raw_transcript, _ = parse_whisper_result(result)
            whisper_language = "hi"

        language = detect_mixed_language(raw_transcript, whisper_language)
        transcript, corrections_made = cleanup_transcript_with_groq(raw_transcript)

        return {
            "transcript": transcript,
            "raw_transcript": raw_transcript,
            "language": language,
            "corrections_made": corrections_made,
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "Transcription failed for upload filename=%s",
            file.filename,
        )
        return transcription_error_response(
            500,
            "transcription_failed",
            str(exc),
        )
    finally:
        # Always close the upload handle and remove the temporary file.
        await file.close()

        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)

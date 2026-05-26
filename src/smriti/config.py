import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    twilio_account_sid: str = os.environ.get("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.environ.get("TWILIO_AUTH_TOKEN", "")
    twilio_whatsapp_from: str = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
    openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
    groq_api_key: str = os.environ.get("GROQ_API_KEY", "")
    elevenlabs_api_key: str = os.environ.get("ELEVENLABS_API_KEY", "")
    shotstack_api_key: str = os.environ.get("SHOTSTACK_API_KEY", "")
    # Replicate hosts the open-source photo models (GFPGAN, Real-ESRGAN, DeOldify).
    # Absent → photo restoration is skipped; the vision story-seed still runs on Groq.
    replicate_api_token: str = os.environ.get("REPLICATE_API_TOKEN", "")
    # Groq vision model for reading a photo and drafting a story seed + elicitation questions.
    vision_model: str = os.environ.get("VISION_MODEL", "llama-3.2-90b-vision-preview")
    # "groq" (free) or "openai"
    transcription_provider: str = os.environ.get("TRANSCRIPTION_PROVIDER", "groq")
    database_url: str = os.environ.get("DATABASE_URL", "sqlite:///smriti.db")
    webhook_base_url: str = os.environ.get("WEBHOOK_BASE_URL", "http://localhost:8000")
    port: int = int(os.environ.get("PORT", "8000"))
    validate_twilio_signature: bool = os.environ.get("VALIDATE_TWILIO_SIGNATURE", "true").lower() == "true"
    books_dir: str = os.environ.get("BOOKS_DIR", "books")
    cron_secret: str = os.environ.get("CRON_SECRET", "")
    admin_key: str = os.environ.get("ADMIN_KEY", "")
    # ElevenLabs voice IDs per language (set after manual voice setup)
    elevenlabs_voice_hindi: str = os.environ.get("ELEVENLABS_VOICE_HINDI", "ThT5KcBeYPX3keUQqHPh")   # Nicole
    elevenlabs_voice_english: str = os.environ.get("ELEVENLABS_VOICE_ENGLISH", "21m00Tcm4TlvDq8ikWAM") # Rachel
    elevenlabs_voice_punjabi: str = os.environ.get("ELEVENLABS_VOICE_PUNJABI", "ThT5KcBeYPX3keUQqHPh") # Nicole


config = Config()

for _name, _val in [
    ("TWILIO_ACCOUNT_SID", config.twilio_account_sid),
    ("TWILIO_AUTH_TOKEN", config.twilio_auth_token),
    ("GROQ_API_KEY", config.groq_api_key),
]:
    if not _val:
        logger.warning("Config: %s is not set — related features will fail at runtime", _name)

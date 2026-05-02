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
    database_url: str = os.environ.get("DATABASE_URL", "sqlite:///smriti.db")
    webhook_base_url: str = os.environ.get("WEBHOOK_BASE_URL", "http://localhost:8000")
    port: int = int(os.environ.get("PORT", "8000"))
    # Set to False in tests; True in production
    validate_twilio_signature: bool = os.environ.get("VALIDATE_TWILIO_SIGNATURE", "true").lower() == "true"
    books_dir: str = os.environ.get("BOOKS_DIR", "books")
    cron_secret: str = os.environ.get("CRON_SECRET", "")


config = Config()

for _name, _val in [
    ("TWILIO_ACCOUNT_SID", config.twilio_account_sid),
    ("TWILIO_AUTH_TOKEN", config.twilio_auth_token),
    ("OPENAI_API_KEY", config.openai_api_key),
]:
    if not _val:
        logger.warning("Config: %s is not set — related features will fail at runtime", _name)

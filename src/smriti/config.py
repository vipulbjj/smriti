import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    twilio_account_sid: str = os.environ.get("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.environ.get("TWILIO_AUTH_TOKEN", "")
    twilio_whatsapp_from: str = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
    openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
    database_url: str = os.environ.get("DATABASE_URL", "sqlite:///smriti.db")
    webhook_base_url: str = os.environ.get("WEBHOOK_BASE_URL", "http://localhost:8000")
    port: int = int(os.environ.get("PORT", "8000"))


config = Config()

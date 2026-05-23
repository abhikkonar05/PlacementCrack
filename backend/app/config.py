from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    MONGODB_URI: str = "mongodb://localhost:27017/placementcrack"
    JWT_SECRET_KEY: str = "supersecretjwtkeyplacementcrack2026version"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    GEMINI_API_KEY: Optional[str] = ""
    HUGGINGFACE_API_TOKEN: Optional[str] = ""
    HUGGINGFACE_MODEL_ID: str = "HuggingFaceH4/zephyr-7b-beta"
    HUGGINGFACE_ASR_MODEL_ID: str = "openai/whisper-large-v3-turbo"
    DEVELOPER_MODE: bool = True

    # Twilio Settings (Optional - falls back to Developer Sandbox mode if empty)
    TWILIO_ACCOUNT_SID: Optional[str] = ""
    TWILIO_AUTH_TOKEN: Optional[str] = ""
    TWILIO_PHONE_NUMBER: Optional[str] = ""

    # SMTP Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    RESEND_API_KEY: Optional[str] = ""
    FROM_EMAIL: str = "PlacementCrack <onboarding@resend.dev>"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/placementcrack"
    JWT_SECRET_KEY: str = "supersecretjwtkeyplacementcrack2026version"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    GROK_API_KEY: Optional[str] = ""
    HUGGINGFACE_API_TOKEN: Optional[str] = ""
    HUGGINGFACE_MODEL_ID: str = "HuggingFaceH4/zephyr-7b-beta"
    HUGGINGFACE_ASR_MODEL_ID: str = "openai/whisper-large-v3-turbo"
    DEVELOPER_MODE: bool = True



    # Email Settings (Resend)
    RESEND_API_KEY: Optional[str] = ""
    FROM_EMAIL: str = "PlacementCrack <onboarding@resend.dev>"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
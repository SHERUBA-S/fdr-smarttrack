from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "FDR SmartTrack"
    API_V1_PREFIX: str = "/api/v1"
    
    SECRET_KEY: str = "fdr_smarttrack_super_secret_jwt_key_2026_sih_hackathon_secure"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # Database URLs
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5433/fdr_smarttrack_db"
    TEST_DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5433/fdr_smarttrack_test_db"

    # File uploads
    UPLOAD_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/uploads"))
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".png", ".jpg", ".jpeg"]
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/jpg"
    ]

    # OCR and AI
    TESSERACT_CMD: str = ""
    ENABLE_ANOMALY_MODEL: bool = True

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000"
    ]

    # Scheduler and alerts
    ENABLE_BACKGROUND_SCHEDULER: bool = True
    ALERT_WINDOWS_DAYS: List[int] = [90, 60, 30, 7, 1]

    # SMTP / Notifications
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@fdr-smarttrack.local"

    model_config = SettingsConfigDict(
        env_file=os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.env")),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure uploads directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

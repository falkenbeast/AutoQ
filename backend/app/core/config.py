import json
import os
from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for the backend (AutoQ/backend)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Default SQLite database location: backend/app/database/autoq.db
DEFAULT_DB_FILE = BASE_DIR / "app" / "database" / "autoq.db"


class Settings(BaseSettings):
    # Application Info
    PROJECT_NAME: str = "AutoQ – Automotive Quality Intelligence API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    DESCRIPTION: str = (
        "Enterprise REST API for AutoQ – Automotive Quality Intelligence System. "
        "Provides component inspection records management, machine learning defect prediction, "
        "manufacturing quality analytics, and inspection audit report services."
    )

    # API Configuration
    API_V1_STR: str = "/api/v1"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Database Configuration (SQLite Foundation at backend/app/database/autoq.db)
    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_FILE.as_posix()}"

    # Storage Paths
    MODEL_STORAGE_PATH: str = str(BASE_DIR / "trained_models")
    DATASET_STORAGE_PATH: str = str(BASE_DIR / "datasets")
    REPORT_STORAGE_PATH: str = str(BASE_DIR / "reports")

    @field_validator("REPORT_STORAGE_PATH", "MODEL_STORAGE_PATH", "DATASET_STORAGE_PATH", mode="before")
    @classmethod
    def resolve_storage_paths(cls, v: str) -> str:
        if not v:
            return v
        clean_v = str(v).replace("\\", "/").strip()
        if clean_v.startswith("backend/"):
            clean_v = clean_v[len("backend/"):].lstrip("/")
        p = Path(clean_v)
        if p.is_absolute():
            return str(p.resolve())
        return str((BASE_DIR / p).resolve())

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, str) and v.startswith("["):
            return json.loads(v)
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()

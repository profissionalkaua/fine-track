from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PULSO_", env_file=ROOT / ".env", extra="ignore")
    environment: str = "development"
    database_url: str = "postgresql+psycopg://pulso_app:pulso-local-only@127.0.0.1:55432/pulso"
    admin_database_url: str = "postgresql+psycopg://postgres:pulso-local-only@127.0.0.1:55432/pulso"
    app_role_password: str = "pulso-local-only"
    origin: str = "http://127.0.0.1:3000"
    cookie_secure: bool = False
    session_hours: int = 24
    collection_enabled: bool = False
    ms_token: str | None = None
    broker_url: str = "amqp://guest:guest@127.0.0.1:5672//"
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = ""
    vision_model: str = ""
    vision_max_frames: int = Field(default=4, ge=1, le=16)
    latest_snapshot_hours: float = 2
    media_root: str = str(ROOT / ".runtime/media")
    media_temp_root: str = str(ROOT / ".runtime/media-work")
    media_max_mb: int = 100
    media_max_seconds: int = 180
    whisper_model_path: str = ""
    pose_model_path: str = ""
    ocr_executable: str = ""
    ocr_languages: str = "por+eng"
    telemetry_enabled: bool = False
    retention_days: int = 90
    classifier_model: str = ""
    classifier_calibrated: bool = False

    @classmethod
    def testing(cls):
        return cls(
            environment="test",
            database_url=cls.model_fields["database_url"].default + "_test",
            admin_database_url=cls.model_fields["admin_database_url"].default + "_test",
            collection_enabled=False,
            ollama_model="",
            vision_model="",
            classifier_model="",
            whisper_model_path="",
            pose_model_path="",
            ocr_executable="",
        )

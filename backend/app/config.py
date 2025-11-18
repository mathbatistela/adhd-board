"""Application configuration using environment variables (12-factor app)."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _resolve_env_file() -> Path | None:
    """Find the repository-level .env (falls back to backend/.env)."""
    repo_root = Path(__file__).resolve().parents[2]
    backend_root = Path(__file__).resolve().parents[1]

    for candidate in (repo_root / ".env", backend_root / ".env"):
        if candidate.exists():
            return candidate
    return None


ENV_FILE = _resolve_env_file()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Flask settings
    flask_env: Literal["development", "production", "testing"] = "development"
    secret_key: str = Field(default="dev-secret-key-change-in-production")
    debug: bool = Field(default=False)

    # Database settings
    database_url: str = Field(
        default="postgresql://adhd:adhd@localhost:5432/adhd_printer",
        description="Database URL (supports PostgreSQL or SQLite for testing)",
    )

    # Printer settings
    printer_encoding: str = Field(default="utf-8")
    printer_enabled: bool = Field(
        default=True, description="Enable/disable actual printer communication (auto-detects USB config)"
    )

    # Thermal printer specs
    max_thermal_width_px: int = Field(default=384)
    thermal_dpi: int = Field(default=203)
    bottom_margin_mm: float = Field(default=15.0)

    # Application settings
    upload_folder: Path = Field(default=Path("uploads"))
    max_content_length: int = Field(default=16 * 1024 * 1024)  # 16 MB

    # Pagination
    default_page_size: int = Field(default=20)
    max_page_size: int = Field(default=100)

    # API settings
    api_title: str = Field(default="adhd Printer API")
    api_version: str = Field(default="1.0.0")
    openapi_version: str = Field(default="3.1.0")

    # CORS settings
    cors_origins: str = Field(default="*")

    def get_cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

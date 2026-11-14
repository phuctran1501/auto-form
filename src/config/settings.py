"""Application configuration settings."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for auto-form execution."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    form_url: str = (
        "https://docs.google.com/forms/d/e/"
        "1FAIpQLSe8OrzsQIgvpg5WiN4U6HoLk8qarpXt5qp08sgVB81QLaNCrQ/viewform"
    )
    headless: bool = True
    delay_min_seconds: int = 30  # 30 seconds
    delay_max_seconds: int = 60  # 1 minute
    state_file_path: Path = Path("data/state/run_progress.json")
    samples_file_path: Path = Path("data/samples/ctu_survey_200.json")
    screenshots_dir: Path = Path("logs/screenshots")
    log_level: str = "INFO"


settings = Settings()

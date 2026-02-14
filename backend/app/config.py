"""Application configuration."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_dir: str = "data"

    # Security
    import_api_key: str | None = None

    # Rate Limiting
    rate_limit_default: str = "100/minute"
    rate_limit_search: str = "30/minute"
    rate_limit_genres: str = "20/minute"
    rate_limit_stats: str = "10/minute"
    rate_limit_poster: str = "200/minute"
    rate_limit_import: str = "5/minute"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        """Get the database URL."""
        db_path = Path(self.database_dir) / "movies.db"
        return f"sqlite:///{db_path}"


settings = Settings()

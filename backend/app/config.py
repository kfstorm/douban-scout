"""Application configuration."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_dir: str = Field(default="data", description="Directory containing the database file")

    # Security
    import_api_key: str | None = Field(
        default=None, description="Secret key required for import API authentication"
    )

    # Rate Limiting
    rate_limit_default: str = Field(default="100/minute", description="Global default rate limit")
    rate_limit_search: str = Field(
        default="30/minute", description="Limit for search and movie list endpoints"
    )
    rate_limit_genres: str = Field(default="20/minute", description="Limit for genres endpoint")
    rate_limit_stats: str = Field(default="10/minute", description="Limit for stats endpoint")
    rate_limit_poster: str = Field(
        default="200/minute", description="Limit for poster proxy endpoint"
    )
    rate_limit_import: str = Field(
        default="5/minute", description="Limit for data import endpoints"
    )

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

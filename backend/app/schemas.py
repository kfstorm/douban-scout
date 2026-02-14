"""Pydantic schemas for API request/response models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class MovieBase(BaseModel):
    """Base movie schema with common fields."""

    id: int
    title: str
    year: int | None = None
    rating: float | None = None
    rating_count: int = 0
    type: Literal["movie", "tv"]
    genres: list[str] = []


class MovieResponse(MovieBase):
    """Movie response schema with additional fields."""

    updated_at: int | None = None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class MoviesListResponse(BaseModel):
    """Response schema for movie list endpoint."""

    items: list[MovieResponse]
    next_cursor: str | None = None
    total: int


class GenreCount(BaseModel):
    """Genre count schema."""

    genre: str
    count: int


class ImportStatus(BaseModel):
    """Import process status schema."""

    status: Literal["idle", "running", "completed", "failed"]
    processed: int = 0
    total: int = 0
    percentage: float = 0.0
    message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class StatsResponse(BaseModel):
    """Database statistics response schema."""

    total_movies: int
    total_tv: int
    avg_rating: float
    total_genres: int

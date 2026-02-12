from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class MovieBase(BaseModel):
    douban_id: str
    imdb_id: Optional[str] = None
    title: str
    year: Optional[int] = None
    rating: Optional[float] = None
    rating_count: int = 0
    type: Literal["movie", "tv"]
    poster_url: Optional[str] = None
    douban_url: str
    genres: List[str] = []


class MovieResponse(MovieBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MoviesListResponse(BaseModel):
    items: List[MovieResponse]
    next_cursor: Optional[str] = None
    total: int


class GenreCount(BaseModel):
    genre: str
    count: int


class ImportStatus(BaseModel):
    status: Literal["idle", "running", "completed", "failed"]
    processed: int = 0
    total: int = 0
    percentage: float = 0.0
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class StatsResponse(BaseModel):
    total_movies: int
    total_tv: int
    avg_rating: float
    total_genres: int

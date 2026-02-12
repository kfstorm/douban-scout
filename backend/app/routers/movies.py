from fastapi import APIRouter, Depends, Query
from typing import List, Optional, Literal
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.movie_service import movie_service
from app.schemas import MoviesListResponse, GenreCount, StatsResponse

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("", response_model=MoviesListResponse)
def get_movies(
    cursor: Optional[str] = Query(None, description="Cursor for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page"),
    type: Optional[Literal["movie", "tv"]] = Query(None, description="Filter by type"),
    min_rating: Optional[float] = Query(
        None, ge=0, le=10, description="Minimum rating"
    ),
    max_rating: Optional[float] = Query(
        None, ge=0, le=10, description="Maximum rating"
    ),
    min_rating_count: Optional[int] = Query(
        None, ge=0, description="Minimum rating count"
    ),
    genres: Optional[str] = Query(
        None, description="Comma-separated genres (AND logic)"
    ),
    search: Optional[str] = Query(None, description="Search in title"),
    sort_by: Literal["rating", "rating_count", "year", "title"] = Query(
        "rating", description="Sort field"
    ),
    sort_order: Literal["asc", "desc"] = Query("desc", description="Sort order"),
    db: Session = Depends(get_db),
):
    genre_list = genres.split(",") if genres else None

    return movie_service.get_movies(
        db=db,
        cursor=cursor,
        limit=limit,
        type=type,
        min_rating=min_rating,
        max_rating=max_rating,
        min_rating_count=min_rating_count,
        genres=genre_list,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/genres", response_model=List[GenreCount])
def get_genres(
    type: Optional[Literal["movie", "tv"]] = Query(None, description="Filter by type"),
    db: Session = Depends(get_db),
):
    return movie_service.get_genres(db, type)


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    return movie_service.get_stats(db)

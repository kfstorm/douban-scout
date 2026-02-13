"""Movie API endpoints."""

from typing import Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import Movie, get_db
from app.schemas import GenreCount, MoviesListResponse, StatsResponse
from app.services.movie_service import movie_service

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("", response_model=MoviesListResponse)
def get_movies(  # noqa: PLR0913
    cursor: str | None = Query(None, description="Cursor for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page"),
    type: Literal["movie", "tv"] | None = Query(None, description="Filter by type"),
    min_rating: float | None = Query(None, ge=0, le=10, description="Minimum rating"),
    max_rating: float | None = Query(None, ge=0, le=10, description="Maximum rating"),
    min_rating_count: int | None = Query(None, ge=0, description="Minimum rating count"),
    genres: str | None = Query(None, description="Comma-separated genres (AND logic)"),
    search: str | None = Query(None, description="Search in title"),
    sort_by: Literal["rating", "rating_count", "year", "title"] = Query(
        "rating", description="Sort field"
    ),
    sort_order: Literal["asc", "desc"] = Query("desc", description="Sort order"),
    db: Session = Depends(get_db),  # noqa: B008
) -> MoviesListResponse:
    """Get movies with filtering and pagination."""
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


@router.get("/genres", response_model=list[GenreCount])
def get_genres(
    type: Literal["movie", "tv"] | None = Query(None, description="Filter by type"),
    db: Session = Depends(get_db),  # noqa: B008
) -> list[GenreCount]:
    """Get all genres with counts."""
    return movie_service.get_genres(db, type)


@router.get("/stats", response_model=StatsResponse)
def get_stats(
    db: Session = Depends(get_db),  # noqa: B008
) -> StatsResponse:
    """Get database statistics."""
    return movie_service.get_stats(db)


@router.get("/{douban_id}/poster")
async def get_poster(
    douban_id: str,
    db: Session = Depends(get_db),  # noqa: B008
) -> StreamingResponse:
    """Proxy poster images from Douban to bypass CORS restrictions.

    Fetches the poster_url from the database for the given douban_id,
    then proxies the image from Douban's CDN.
    """
    # Fetch poster_url from database
    movie = db.query(Movie).filter(Movie.douban_id == douban_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    if not movie.poster_url:
        raise HTTPException(status_code=404, detail="No poster available for this movie")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Referer": "https://movie.douban.com/",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(movie.poster_url, headers=headers, timeout=10.0)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "image/jpeg")
            return StreamingResponse(
                response.aiter_bytes(),
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=86400",
                },
            )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch poster: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}") from e

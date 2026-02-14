"""Movie API endpoints."""

import re
from typing import Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask

from app.cache import cached
from app.config import settings
from app.database import Movie, MoviePoster, get_db
from app.limiter import limiter
from app.schemas import GenreCount, MoviesListResponse, StatsResponse
from app.services.movie_service import movie_service

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("", response_model=MoviesListResponse)
@limiter.limit(settings.rate_limit_search)
def get_movies(  # noqa: PLR0913
    request: Request,
    cursor: str | None = Query(None, description="Cursor for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page"),
    type: Literal["movie", "tv"] | None = Query(None, description="Filter by type"),
    min_rating: float | None = Query(None, ge=0, le=10, description="Minimum rating"),
    max_rating: float | None = Query(None, ge=0, le=10, description="Maximum rating"),
    min_rating_count: int | None = Query(None, ge=0, description="Minimum rating count"),
    min_year: int | None = Query(None, description="Minimum year"),
    max_year: int | None = Query(None, description="Maximum year"),
    genres: str | None = Query(None, description="Comma-separated genres (AND logic)"),
    exclude_genres: str | None = Query(
        None, description="Comma-separated genres to exclude (OR logic)"
    ),
    search: str | None = Query(None, description="Search in title"),
    sort_by: Literal["rating", "rating_count", "year"] = Query("rating", description="Sort field"),
    sort_order: Literal["asc", "desc"] = Query("desc", description="Sort order"),
    db: Session = Depends(get_db),  # noqa: B008
) -> MoviesListResponse:
    """Get movies with filtering and pagination."""
    genre_list = genres.split(",") if genres else None
    exclude_genre_list = exclude_genres.split(",") if exclude_genres else None

    return movie_service.get_movies(
        db=db,
        cursor=cursor,
        limit=limit,
        type=type,
        min_rating=min_rating,
        max_rating=max_rating,
        min_rating_count=min_rating_count,
        min_year=min_year,
        max_year=max_year,
        genres=genre_list,
        exclude_genres=exclude_genre_list,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/genres", response_model=list[GenreCount])
@limiter.limit(settings.rate_limit_genres)
def get_genres(
    request: Request,
    type: Literal["movie", "tv"] | None = Query(None, description="Filter by type"),
    db: Session = Depends(get_db),  # noqa: B008
) -> list[GenreCount]:
    """Get all genres with counts."""
    return movie_service.get_genres(db, type)


@router.get("/stats", response_model=StatsResponse)
@limiter.limit(settings.rate_limit_stats)
def get_stats(
    request: Request,
    db: Session = Depends(get_db),  # noqa: B008
) -> StatsResponse:
    """Get database statistics."""
    return movie_service.get_stats(db)


def _get_poster_candidates(base_urls: list[str]) -> list[str]:
    """Generate all candidate URLs including mirror fallbacks."""
    all_candidates = []
    for base_url in base_urls:
        all_candidates.append(base_url)
        # If it's an img[0-9]+.doubanio.com URL, add fallbacks
        match = re.search(r"img([0-9]+)\.doubanio\.com", base_url)
        if match:
            original_host = match.group(0)
            # Douban uses img1, img2, and img3 as reliable mirrors.
            for i in ["1", "2", "3"]:
                new_host = f"img{i}.doubanio.com"
                if new_host != original_host:
                    fallback_url = base_url.replace(original_host, new_host)
                    if fallback_url not in all_candidates:
                        all_candidates.append(fallback_url)
    return all_candidates


@cached(prefix="working_poster")
async def _find_working_poster_url(poster_urls: list[str]) -> tuple[str, str] | None:
    """Find the first working poster URL and its content type."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Referer": "https://movie.douban.com/",
    }

    async with httpx.AsyncClient() as client:
        urls_to_try = _get_poster_candidates(poster_urls)
        for url in urls_to_try:
            try:
                # Use HEAD first to check if it's an image and if it exists
                # Some CDN might not support HEAD well, so we might fallback to GET
                response = await client.get(url, headers=headers, timeout=5.0)
                response.raise_for_status()

                content_type = response.headers.get("content-type", "")
                if content_type.startswith("image/"):
                    return url, content_type
            except httpx.HTTPError:
                continue
    return None


@router.get("/{id}/poster")
@limiter.limit(settings.rate_limit_poster)
async def get_poster(
    request: Request,
    id: int,
    db: Session = Depends(get_db),  # noqa: B008
) -> StreamingResponse:
    """Proxy poster images from Douban to bypass CORS restrictions.

    Fetches poster URLs from the database for the given id,
    then proxies the first working image from Douban's CDN.
    """
    # Fetch movie and all poster URLs from database
    movie = db.query(Movie).filter(Movie.id == id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    posters = db.query(MoviePoster).filter(MoviePoster.movie_id == movie.id).all()
    poster_urls = [p.url for p in posters]

    if not poster_urls:
        raise HTTPException(status_code=404, detail="No poster available for this movie")

    result = await _find_working_poster_url(poster_urls)
    if not result:
        raise HTTPException(status_code=502, detail="Failed to fetch a valid poster image")

    working_url, content_type = result

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Referer": "https://movie.douban.com/",
    }

    try:
        # We don't use the client from _find_working_poster_url to keep it simple
        # and because StreamingResponse needs an open stream.
        client = httpx.AsyncClient()
        response = await client.get(working_url, headers=headers, timeout=10.0)
        response.raise_for_status()

        return StreamingResponse(
            response.aiter_bytes(),
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=86400",
            },
            background=BackgroundTask(client.aclose),
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch poster: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}") from e

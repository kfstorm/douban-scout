"""Movie service with business logic."""

import base64
import json
import logging

from sqlalchemy import func, text
from sqlalchemy.orm import Session, selectinload

from app.database import Genre, Movie, MovieGenre
from app.schemas import GenreCount, MovieResponse, MoviesListResponse, StatsResponse

logger = logging.getLogger("douban.movies")

MAX_RATING = 10.0


class MovieService:
    """Service for movie-related operations."""

    @staticmethod
    def get_movies(  # noqa: PLR0912, PLR0913, PLR0915
        db: Session,
        cursor: str | None = None,
        limit: int = 20,
        type: str | None = None,
        min_rating: float | None = None,
        max_rating: float | None = None,
        min_rating_count: int | None = None,
        min_year: int | None = None,
        max_year: int | None = None,
        genres: list[str] | None = None,
        exclude_genres: list[str] | None = None,
        search: str | None = None,
        sort_by: str = "rating",
        sort_order: str = "desc",
    ) -> MoviesListResponse:
        """Get movies with filtering and pagination."""
        logger.debug(
            f"Querying movies with filters: type={type}, genres={genres}, "
            f"exclude_genres={exclude_genres}, search={search}"
        )
        # Eager load genres to avoid N+1
        query = db.query(Movie).options(
            selectinload(Movie.genres).selectinload(MovieGenre.genre_obj)
        )

        # Apply search first using FTS5 if available
        if search:
            # Note: We use raw SQL for FTS5 because it's a virtual table
            # We filter by ID using the search results
            search_query = text(
                "SELECT rowid FROM movie_search WHERE movie_search MATCH :search_term"
            )
            # Escape search term for FTS5 (simple version, could be more robust)
            # FTS5 MATCH usually prefers quoted terms for exact matches or specific syntax
            # For simplicity, we'll just pass it through
            query = query.filter(
                Movie.id.in_(db.execute(search_query, {"search_term": search}).scalars().all())
            )

        # Apply filters
        if type:
            query = query.filter(Movie.type == type)

        # Rating filters
        # When min_rating is not set or 0, include NULL ratings
        # When min_rating > 0, exclude NULL ratings
        effective_min = min_rating if min_rating is not None else 0
        effective_max = max_rating if max_rating is not None else MAX_RATING

        if effective_min > 0:
            # Exclude NULL ratings when min > 0
            query = query.filter(Movie.rating.isnot(None))
            query = query.filter(Movie.rating.between(effective_min, effective_max))
        elif effective_max < MAX_RATING:
            # Include NULL ratings, but filter by max_rating
            query = query.filter(
                ((Movie.rating >= 0) & (Movie.rating <= effective_max)) | (Movie.rating.is_(None))
            )
        # else: effective_min=0 and effective_max=10, no filter needed

        if min_rating_count is not None:
            query = query.filter(Movie.rating_count >= min_rating_count)

        # Year filters
        # When min_year is not set, include NULL years
        # When min_year is set, exclude NULL years
        if min_year is not None:
            query = query.filter(Movie.year.isnot(None))
            if max_year is not None:
                query = query.filter(Movie.year.between(min_year, max_year))
            else:
                query = query.filter(Movie.year >= min_year)
        elif max_year is not None:
            query = query.filter((Movie.year <= max_year) | (Movie.year.is_(None)))

        # AND logic for genres (Optimized with JOIN + GROUP BY)
        if genres:
            query = (
                query.join(Movie.genres).join(MovieGenre.genre_obj).filter(Genre.name.in_(genres))
            )
            query = query.group_by(Movie.id).having(func.count(Genre.id) == len(genres))

        # Exclusion logic for genres
        if exclude_genres:
            for g_name in exclude_genres:
                query = query.filter(
                    ~Movie.id.in_(
                        db.query(MovieGenre.movie_id).join(Genre).filter(Genre.name == g_name)
                    )
                )

        # Get total count (before pagination)
        # For GROUP BY queries, we need a special count
        if genres:
            total = db.query(func.count()).select_from(query.subquery()).scalar() or 0
        else:
            total = query.count()

        # Cursor-based pagination
        if cursor:
            try:
                cursor_data = json.loads(base64.b64decode(cursor.encode()).decode())
                cursor_value = cursor_data.get("value")
                cursor_id = cursor_data.get("id")

                sort_column = getattr(Movie, sort_by, Movie.rating)

                if sort_order == "desc":
                    if cursor_value is not None:
                        query = query.filter(
                            (sort_column < cursor_value)
                            | (sort_column.is_(None))
                            | ((sort_column == cursor_value) & (Movie.id < cursor_id))
                        )
                    else:
                        query = query.filter((sort_column.is_(None)) & (Movie.id < cursor_id))
                elif cursor_value is not None:
                    query = query.filter(
                        (sort_column > cursor_value)
                        | ((sort_column == cursor_value) & (Movie.id > cursor_id))
                    )
                else:
                    query = query.filter(
                        (sort_column.isnot(None))
                        | ((sort_column.is_(None)) & (Movie.id > cursor_id))
                    )
            except (json.JSONDecodeError, ValueError):
                pass  # Invalid cursor, ignore

        # Sorting
        sort_column = getattr(Movie, sort_by, Movie.rating)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc(), Movie.id.desc())
        else:
            query = query.order_by(sort_column.asc(), Movie.id.asc())

        # Fetch items
        items = query.limit(limit + 1).all()

        has_more = len(items) > limit
        items = items[:limit]

        # Build response
        movie_responses = []
        for movie in items:
            # Map normalized genres back to list of strings
            movie_genres: list[str] = [g.genre_obj.name for g in movie.genres]
            movie_responses.append(
                MovieResponse(
                    id=movie.id,
                    title=movie.title,
                    year=movie.year,
                    rating=movie.rating,
                    rating_count=movie.rating_count,
                    type=movie.type,
                    genres=movie_genres,
                    updated_at=movie.updated_at,
                )
            )

        # Generate next cursor
        next_cursor = None
        if has_more and items:
            last_item = items[-1]
            cursor_value = getattr(last_item, sort_by)
            cursor_data = {"value": cursor_value, "id": last_item.id}
            next_cursor = base64.b64encode(json.dumps(cursor_data).encode()).decode()

        logger.debug(f"Returning {len(movie_responses)} movies (total: {total})")
        return MoviesListResponse(items=movie_responses, next_cursor=next_cursor, total=total)

    @staticmethod
    def get_genres(db: Session, type: str | None = None) -> list[GenreCount]:
        """Get all genres with counts."""
        logger.debug(f"Querying genres with type filter: {type}")
        query = db.query(Genre.name, func.count(MovieGenre.movie_id).label("count")).join(
            Genre.movie_associations
        )

        if type:
            query = query.join(MovieGenre.movie).filter(Movie.type == type)

        results = query.group_by(Genre.name).order_by(func.count(MovieGenre.movie_id).desc()).all()

        return [GenreCount(genre=r[0], count=r[1]) for r in results]

    @staticmethod
    def get_stats(db: Session) -> StatsResponse:
        """Get database statistics."""
        logger.debug("Querying database statistics")
        total_movies = db.query(Movie).filter(Movie.type == "movie").count()
        total_tv = db.query(Movie).filter(Movie.type == "tv").count()
        avg_rating = db.query(func.avg(Movie.rating)).scalar() or 0.0
        total_genres = db.query(Genre).count()

        logger.info(f"Stats: {total_movies} movies, {total_tv} TV shows, {total_genres} genres")
        return StatsResponse(
            total_movies=total_movies,
            total_tv=total_tv,
            avg_rating=round(avg_rating, 2),
            total_genres=total_genres,
        )


movie_service = MovieService()

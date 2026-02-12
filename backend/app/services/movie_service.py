from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.database import Movie, MovieGenre
from app.schemas import MovieResponse, MoviesListResponse, GenreCount, StatsResponse
import base64
import json


class MovieService:
    VALID_GENRES = {
        "剧情",
        "喜剧",
        "爱情",
        "动作",
        "惊悚",
        "犯罪",
        "恐怖",
        "动画",
        "纪录片",
        "短片",
        "悬疑",
        "冒险",
        "科幻",
        "奇幻",
        "家庭",
        "音乐",
        "历史",
        "战争",
        "歌舞",
        "传记",
        "古装",
        "真人秀",
        "同性",
        "运动",
        "西部",
        "情色",
        "儿童",
        "武侠",
        "脱口秀",
        "黑色电影",
        "戏曲",
        "灾难",
    }

    @staticmethod
    def get_movies(
        db: Session,
        cursor: Optional[str] = None,
        limit: int = 20,
        type: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_rating: Optional[float] = None,
        min_rating_count: Optional[int] = None,
        genres: Optional[List[str]] = None,
        search: Optional[str] = None,
        sort_by: str = "rating",
        sort_order: str = "desc",
    ) -> MoviesListResponse:
        query = db.query(Movie)

        # Apply filters
        if type:
            query = query.filter(Movie.type == type)

        if min_rating is not None:
            query = query.filter(Movie.rating >= min_rating)

        if max_rating is not None:
            query = query.filter(Movie.rating <= max_rating)

        if min_rating_count is not None:
            query = query.filter(Movie.rating_count >= min_rating_count)

        if search:
            query = query.filter(Movie.title.ilike(f"%{search}%"))

        # AND logic for genres
        if genres:
            valid_genres = [g for g in genres if g in MovieService.VALID_GENRES]
            if valid_genres:
                for genre in valid_genres:
                    query = query.filter(
                        Movie.id.in_(
                            db.query(MovieGenre.movie_id).filter(
                                MovieGenre.genre == genre
                            )
                        )
                    )

        # Get total count
        total = query.count()

        # Cursor-based pagination
        if cursor:
            try:
                cursor_data = json.loads(base64.b64decode(cursor.encode()).decode())
                cursor_value = cursor_data.get("value")
                cursor_id = cursor_data.get("id")

                if sort_order == "desc":
                    query = query.filter(
                        and_(
                            getattr(Movie, sort_by) < cursor_value
                            if cursor_value
                            else True,
                            Movie.id < cursor_id,
                        )
                        if cursor_value
                        else Movie.id < cursor_id
                    )
                else:
                    query = query.filter(
                        and_(
                            getattr(Movie, sort_by) > cursor_value
                            if cursor_value
                            else True,
                            Movie.id > cursor_id,
                        )
                        if cursor_value
                        else Movie.id > cursor_id
                    )
            except:
                pass

        # Sorting
        sort_column = getattr(Movie, sort_by, Movie.rating)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc(), Movie.id.desc())
        else:
            query = query.order_by(sort_column.asc(), Movie.id.asc())

        # Fetch one extra to check if there's more
        items = query.limit(limit + 1).all()

        has_more = len(items) > limit
        items = items[:limit]

        # Build response
        movie_responses = []
        for movie in items:
            genres = [g.genre for g in movie.genres]
            movie_responses.append(
                MovieResponse(
                    id=movie.id,
                    douban_id=movie.douban_id,
                    imdb_id=movie.imdb_id,
                    title=movie.title,
                    year=movie.year,
                    rating=movie.rating,
                    rating_count=movie.rating_count,
                    type=movie.type,
                    poster_url=movie.poster_url,
                    douban_url=movie.douban_url,
                    genres=genres,
                    created_at=movie.created_at,
                )
            )

        # Generate next cursor
        next_cursor = None
        if has_more and items:
            last_item = items[-1]
            cursor_value = getattr(last_item, sort_by)
            cursor_data = {"value": cursor_value, "id": last_item.id}
            next_cursor = base64.b64encode(json.dumps(cursor_data).encode()).decode()

        return MoviesListResponse(
            items=movie_responses, next_cursor=next_cursor, total=total
        )

    @staticmethod
    def get_genres(db: Session, type: Optional[str] = None) -> List[GenreCount]:
        query = db.query(
            MovieGenre.genre, func.count(MovieGenre.movie_id).label("count")
        )

        if type:
            query = query.join(Movie).filter(Movie.type == type)

        results = (
            query.group_by(MovieGenre.genre)
            .order_by(func.count(MovieGenre.movie_id).desc())
            .all()
        )

        return [GenreCount(genre=r[0], count=r[1]) for r in results]

    @staticmethod
    def get_stats(db: Session) -> StatsResponse:
        total_movies = db.query(Movie).filter(Movie.type == "movie").count()
        total_tv = db.query(Movie).filter(Movie.type == "tv").count()
        avg_rating = db.query(func.avg(Movie.rating)).scalar() or 0.0
        total_genres = db.query(MovieGenre.genre).distinct().count()

        return StatsResponse(
            total_movies=total_movies,
            total_tv=total_tv,
            avg_rating=round(avg_rating, 2),
            total_genres=total_genres,
        )


movie_service = MovieService()

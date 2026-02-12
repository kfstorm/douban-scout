import sqlite3
import json
from typing import List, Optional
from sqlalchemy.orm import Session
from app.database import Movie, MovieGenre, engine
from app.schemas import ImportStatus
import threading
from datetime import datetime
import os


class ImportService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._status = ImportStatus(status="idle")
        return cls._instance

    @property
    def status(self) -> ImportStatus:
        return self._status

    def start_import(self, source_path: str) -> ImportStatus:
        with self._lock:
            if self._status.status == "running":
                return self._status

            self._status = ImportStatus(
                status="running",
                processed=0,
                total=0,
                percentage=0.0,
                started_at=datetime.now(),
            )

            thread = threading.Thread(target=self._import_data, args=(source_path,))
            thread.daemon = True
            thread.start()

            return self._status

    def _import_data(self, source_path: str):
        try:
            if not os.path.exists(source_path):
                raise FileNotFoundError(f"Source file not found: {source_path}")

            # Connect to source database
            source_conn = sqlite3.connect(source_path)
            source_cursor = source_conn.cursor()

            # Get total count
            source_cursor.execute("SELECT COUNT(*) FROM item")
            total = source_cursor.fetchone()[0]

            with self._lock:
                self._status.total = total

            # Clear existing data
            with Session(engine) as db:
                db.query(MovieGenre).delete()
                db.query(Movie).delete()
                db.commit()

            # Import in batches
            batch_size = 1000
            processed = 0
            batch = []
            genre_batch = []

            # Valid genres
            valid_genres = {
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

            source_cursor.execute(
                "SELECT douban_id, imdb_id, douban_title, year, rating, raw_data, type "
                "FROM item WHERE type IN ('movie', 'tv')"
            )

            for row in source_cursor:
                douban_id = None
                try:
                    douban_id, imdb_id, title, year, rating, raw_data, item_type = row

                    # Initialize defaults
                    rating_count = 0
                    poster_url = None
                    genres = set()

                    # Parse raw_data JSON
                    if raw_data:
                        data = json.loads(raw_data)
                        detail = data.get("detail", {})

                        # Extract rating count
                        if isinstance(detail, dict):
                            rating_info = detail.get("rating", {})
                            if isinstance(rating_info, dict):
                                rating_count = rating_info.get("count", 0)

                            # Extract poster URL
                            pic = detail.get("pic", {})
                            if isinstance(pic, dict):
                                poster_url = pic.get("normal") or pic.get("large")

                            # Extract genres from card_subtitle
                            card_subtitle = detail.get("card_subtitle", "")
                            if card_subtitle:
                                parts = card_subtitle.split(" / ")
                                if len(parts) >= 3:
                                    genre_part = parts[2]
                                    for g in genre_part.split():
                                        g = g.strip()
                                        if g in valid_genres:
                                            genres.add(g)

                    # Build douban_url
                    douban_url = f"https://movie.douban.com/subject/{douban_id}/"

                    movie = {
                        "douban_id": douban_id,
                        "imdb_id": imdb_id,
                        "title": title or "",
                        "year": year,
                        "rating": rating,
                        "rating_count": rating_count,
                        "type": item_type,
                        "poster_url": poster_url,
                        "douban_url": douban_url,
                        "genres": list(genres),
                    }

                    batch.append(movie)

                    if len(batch) >= batch_size:
                        self._insert_batch(batch, genre_batch)
                        processed += len(batch)
                        batch = []
                        genre_batch = []

                        with self._lock:
                            self._status.processed = processed
                            self._status.percentage = (processed / total) * 100

                except Exception as e:
                    print(f"Error processing row {douban_id}: {e}")
                    continue

            # Insert remaining
            if batch:
                self._insert_batch(batch, genre_batch)
                processed += len(batch)

            source_conn.close()

            with self._lock:
                self._status.status = "completed"
                self._status.processed = processed
                self._status.percentage = 100.0
                self._status.completed_at = datetime.now()

        except Exception as e:
            with self._lock:
                self._status.status = "failed"
                self._status.message = str(e)
                self._status.completed_at = datetime.now()

    def _insert_batch(self, movies: List[dict], genre_batch: List[tuple]):
        with Session(engine) as db:
            for movie_data in movies:
                genres = movie_data.pop("genres", [])

                movie = Movie(**movie_data)
                db.add(movie)
                db.flush()

                for genre in genres:
                    genre_batch.append((movie.id, genre))

            # Bulk insert genres
            if genre_batch:
                db.execute(
                    MovieGenre.__table__.insert(),
                    [{"movie_id": m_id, "genre": g} for m_id, g in genre_batch],
                )

            db.commit()


import_service = ImportService()

"""Data import service with singleton pattern."""

import json
import logging
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import ClassVar

from sqlalchemy.orm import Session

from app import database as app_db
from app.database import Movie, MovieGenre
from app.schemas import ImportStatus

# Configure logger
logger = logging.getLogger("douban.import")


class ImportService:
    """Singleton service for importing movie data."""

    _instance: "ImportService | None" = None
    _lock = threading.Lock()
    _status: ImportStatus

    _MAX_ERROR_LOGS = 10  # Maximum number of errors to log with full traceback

    # Valid genres
    VALID_GENRES: ClassVar[set[str]] = {
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

    def __new__(cls) -> "ImportService":
        """Create singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._status = ImportStatus(status="idle")
        return cls._instance

    @property
    def status(self) -> ImportStatus:
        """Get current import status."""
        return self._status

    def start_import(self, source_path: str) -> ImportStatus:
        """Start the import process in a background thread."""
        with self._lock:
            if self._status.status == "running":
                logger.warning("Import already in progress, cannot start new import")
                return self._status

            logger.info(f"Starting import from: {source_path}")
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

    def _import_data(self, source_path: str) -> None:  # noqa: PLR0912, PLR0915
        """Internal method to perform the import."""
        try:
            logger.info(f"Connecting to source database: {source_path}")
            if not Path(source_path).exists():
                raise FileNotFoundError(f"Source file not found: {source_path}")

            # Connect to source database
            source_conn = sqlite3.connect(source_path)
            source_cursor = source_conn.cursor()

            # Get total count of items to import (movie and tv).
            # Note: Items with empty type are placeholders that only have douban_id set
            # and should be ignored.
            source_cursor.execute("SELECT COUNT(*) FROM item WHERE type IN ('movie', 'tv')")
            total = source_cursor.fetchone()[0]
            logger.info(f"Found {total} total records to import")

            with self._lock:
                self._status.total = total

            with Session(app_db.engine) as db:
                # Clear existing data
                logger.info("Clearing existing data...")
                deleted_genres = db.query(MovieGenre).delete()
                deleted_movies = db.query(Movie).delete()
                logger.info(
                    f"Cleared {deleted_movies} movies and {deleted_genres} genre associations"
                )

                # Import in batches
                batch_size = 1000
                processed = 0
                batch: list[dict] = []
                error_count = 0

                logger.info("Starting data import...")
                source_cursor.execute(
                    "SELECT douban_id, imdb_id, douban_title, year, rating, raw_data, "
                    "type, update_time FROM item WHERE type IN ('movie', 'tv')"
                )

                for row in source_cursor:
                    douban_id = None
                    try:
                        (
                            douban_id,
                            imdb_id,
                            title,
                            year,
                            rating,
                            raw_data,
                            item_type,
                            update_time,
                        ) = row

                        # Initialize defaults
                        rating_count = 0
                        poster_url = None
                        genres: set[str] = set()

                        # Parse raw_data JSON
                        if raw_data:
                            try:
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

                                    if not poster_url:
                                        poster_url = detail.get("cover_url")

                                    # Extract genres from card_subtitle by checking all tokens
                                    card_subtitle = detail.get("card_subtitle", "")
                                    if card_subtitle:
                                        # card_subtitle example: "2000 / 美国 / 剧情 喜剧"
                                        # Split by any whitespace and "/" to get genre tokens
                                        tokens = card_subtitle.replace("/", " ").split()
                                        for token in tokens:
                                            if token in self.VALID_GENRES:
                                                genres.add(token)
                            except json.JSONDecodeError as e:
                                logger.warning(
                                    f"Failed to parse raw_data for douban_id {douban_id}: {e}"
                                )

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
                            "updated_at": int(update_time) if update_time else None,
                        }

                        batch.append(movie)

                        if len(batch) >= batch_size:
                            self._insert_batch(db, batch)
                            processed += len(batch)
                            batch = []

                            with self._lock:
                                self._status.processed = processed
                                if total > 0:
                                    self._status.percentage = (processed / total) * 100
                                else:
                                    self._status.percentage = 100.0

                            if processed % 10000 == 0:
                                pct = self._status.percentage
                                logger.info(f"Imported {processed}/{total} records ({pct:.1f}%)")

                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error processing row {douban_id}: {e}", exc_info=True)
                        if error_count <= self._MAX_ERROR_LOGS:
                            continue
                        else:
                            logger.warning(
                                f"Suppressing detailed error logs after {error_count} errors"
                            )

                # Insert remaining
                if batch:
                    logger.info(f"Inserting final batch of {len(batch)} records...")
                    self._insert_batch(db, batch)
                    processed += len(batch)

                # Commit the entire transaction
                logger.info("Committing transaction...")
                db.commit()

            source_conn.close()

            logger.info(
                f"Import completed successfully. "
                f"Processed {processed} records with {error_count} errors"
            )
            with self._lock:
                self._status.status = "completed"
                self._status.processed = processed
                self._status.percentage = 100.0
                self._status.completed_at = datetime.now()

        except Exception as e:
            logger.exception(f"Import failed: {e}")
            with self._lock:
                self._status.status = "failed"
                self._status.message = str(e)
                self._status.completed_at = datetime.now()

    def _insert_batch(self, db: Session, movies: list[dict]) -> None:
        """Insert a batch of movies and their genres."""
        try:
            for movie_data in movies:
                genres = movie_data.pop("genres", [])

                movie = Movie(**movie_data)
                db.add(movie)
                db.flush()

                for genre in genres:
                    db.add(MovieGenre(movie_id=movie.id, genre=genre))

            db.flush()
            db.expunge_all()
            logger.debug(f"Inserted batch of {len(movies)} movies")
        except Exception as e:
            logger.exception(f"Failed to insert batch: {e}")
            raise


import_service = ImportService()

"""Data import service with singleton pattern."""

import contextlib
import json
import logging
import re
import shutil
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import ClassVar

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app import database
from app.cache import cache_manager
from app.database import (
    FTS_CREATE_TABLE_SQL,
    FTS_INSERT_ALL_SQL,
    FTS_TABLE_NAME,
    Base,
    Genre,
    Movie,
    MovieGenre,
    MoviePoster,
    MovieRegion,
    Region,
    get_db_path,
)
from app.metadata_constants import VALID_GENRES, VALID_REGIONS
from app.schemas import ImportStatus

# Configure logger
logger = logging.getLogger("douban.import")


class ImportService:
    """Singleton service for importing movie data."""

    _instance: "ImportService | None" = None
    _lock = threading.Lock()
    _status: ImportStatus

    _MAX_ERROR_LOGS = 10  # Maximum number of errors to log with full traceback

    # Valid genres and regions from generated constants
    VALID_GENRES: ClassVar[set[str]] = set(VALID_GENRES)
    VALID_REGIONS: ClassVar[set[str]] = set(VALID_REGIONS)

    # Sorted versions for greedy matching (longest first)
    _SORTED_REGIONS: ClassVar[list[str]] = sorted(VALID_REGIONS, key=len, reverse=True)
    _SORTED_GENRES: ClassVar[list[str]] = sorted(VALID_GENRES, key=len, reverse=True)

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
                raise RuntimeError("Import already in progress")

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

    def _extract_metadata_from_string(self, s: str, is_genre: bool = True) -> set[str]:
        """Extract valid genres or regions from a string using greedy matching."""
        if not s:
            return set()

        found = set()
        # Split by major delimiters into segments
        segments = re.split(r"[/|\\,，、]", s)  # noqa: RUF001

        whitelist = self._SORTED_GENRES if is_genre else self._SORTED_REGIONS
        valid_set = self.VALID_GENRES if is_genre else self.VALID_REGIONS

        for seg in segments:
            cleaned_seg = seg.strip().strip("()（）[]:;\"'").strip()  # noqa: RUF001
            if not cleaned_seg:
                continue

            # First try matching the entire segment (handles "Trinidad and Tobago")
            if cleaned_seg in valid_set:
                found.add(cleaned_seg)
                continue

            # If no whole match, find all whitelist items present in the segment
            for item in whitelist:
                if not item:
                    continue
                if item.isascii():
                    # Use word boundaries for English tokens to avoid partial matches
                    pattern = rf"\b{re.escape(item)}\b"
                    if re.search(pattern, cleaned_seg):
                        found.add(item)
                elif item in cleaned_seg:
                    found.add(item)

        return found

    def _import_data(self, source_path: str) -> None:  # noqa: PLR0912, PLR0915
        """Internal method to perform the import."""
        target_db_path = Path(get_db_path())
        temp_db_path = target_db_path.with_suffix(".db.tmp")
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

            # Ensure data directory exists
            temp_db_path.parent.mkdir(parents=True, exist_ok=True)
            if temp_db_path.exists():
                temp_db_path.unlink()

            # Create fresh temp DB with high-speed settings for import
            logger.info(f"Creating temporary database at {temp_db_path}")
            temp_engine = create_engine(
                f"sqlite:///{temp_db_path}",
                connect_args={"check_same_thread": False},
            )

            # Set performance pragmas for the import session
            with temp_engine.connect() as conn:
                # Use DELETE mode for the temp DB to avoid leaving -wal files behind
                conn.execute(text("PRAGMA journal_mode = DELETE"))
                conn.execute(text("PRAGMA synchronous = OFF"))
                conn.execute(text("PRAGMA cache_size = -100000"))  # 100MB cache

            Base.metadata.create_all(bind=temp_engine)  # type: ignore[attr-defined]

            with Session(temp_engine) as db:
                # Pre-populate Genres
                logger.info("Populating genres table...")
                genre_map = {}
                for g_name in sorted(self.VALID_GENRES):
                    genre = Genre(name=g_name)
                    db.add(genre)
                db.flush()

                genres_list = db.query(Genre).all()
                genre_map = {g.name: g.id for g in genres_list}

                # Pre-populate Regions
                logger.info("Populating regions table...")
                for r_name in sorted(self.VALID_REGIONS):
                    region = Region(name=r_name)
                    db.add(region)
                db.flush()

                regions_list = db.query(Region).all()
                region_map = {r.name: r.id for r in regions_list}
                db.commit()

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
                            _,
                            title,
                            year,
                            rating,
                            raw_data,
                            item_type,
                            update_time,
                        ) = row

                        # Initialize defaults
                        rating_count = 0
                        poster_urls: set[str] = set()
                        movie_genre_names: set[str] = set()
                        movie_region_names: set[str] = set()

                        # Parse raw_data JSON
                        if raw_data:
                            try:
                                data = json.loads(raw_data)
                                detail = data.get("detail", {})
                                if isinstance(detail, dict):
                                    # Extract rating count
                                    rating_info = detail.get("rating", {})
                                    if isinstance(rating_info, dict):
                                        rating_count = rating_info.get("count", 0)
                                    if not rating_count:
                                        # Fallback to vote_count (top_list format)
                                        rating_count = detail.get("vote_count", 0)

                                    # Extract poster URLs
                                    pic = detail.get("pic", {})
                                    if isinstance(pic, dict):
                                        for key in ["normal", "large"]:
                                            if pic.get(key):
                                                poster_urls.add(pic[key])

                                    cover_url = detail.get("cover_url")
                                    if cover_url:
                                        poster_urls.add(cover_url)

                                    # Extract regions
                                    countries = detail.get("countries", [])
                                    regions = detail.get("regions", [])
                                    # Handle both "countries" and "regions" as lists
                                    for r in (countries if isinstance(countries, list) else []) + (
                                        regions if isinstance(regions, list) else []
                                    ):
                                        if isinstance(r, str):
                                            movie_region_names.update(
                                                self._extract_metadata_from_string(
                                                    r, is_genre=False
                                                )
                                            )

                                    # Extract genres
                                    genres_list = detail.get("genres", [])
                                    types_list = detail.get("types", [])
                                    # Handle both "genres" and "types" as lists
                                    for g in (
                                        genres_list if isinstance(genres_list, list) else []
                                    ) + (types_list if isinstance(types_list, list) else []):
                                        if isinstance(g, str):
                                            movie_genre_names.update(
                                                self._extract_metadata_from_string(g, is_genre=True)
                                            )

                                    # Extract from card_subtitle or subtitle
                                    card_subtitle = detail.get("card_subtitle") or detail.get(
                                        "subtitle", ""
                                    )
                                    if card_subtitle:
                                        # First identify genres as markers
                                        subtitle_genres = self._extract_metadata_from_string(
                                            card_subtitle, is_genre=True
                                        )
                                        movie_genre_names.update(subtitle_genres)

                                        # Use genres to find region boundaries
                                        parts = [p.strip() for p in card_subtitle.split("/")]
                                        if parts:
                                            start_idx = 1 if re.match(r"^\d{4}$", parts[0]) else 0

                                            # Find the first part containing any identified genre
                                            genre_idx = -1
                                            for i in range(start_idx, len(parts)):
                                                tokens = self._extract_metadata_from_string(
                                                    parts[i], is_genre=True
                                                )
                                                if tokens:
                                                    genre_idx = i
                                                    break

                                            if genre_idx != -1:
                                                # Parts before the first genre are regions
                                                for i in range(start_idx, genre_idx):
                                                    movie_region_names.update(
                                                        self._extract_metadata_from_string(
                                                            parts[i], is_genre=False
                                                        )
                                                    )
                                            elif len(parts) > start_idx:
                                                # Fallback if no genre found
                                                movie_region_names.update(
                                                    self._extract_metadata_from_string(
                                                        parts[start_idx], is_genre=False
                                                    )
                                                )

                                    # Extract from tags
                                    tags = detail.get("tags", [])
                                    if isinstance(tags, list):
                                        for tag in tags:
                                            tag_name = tag.get("name", "")
                                            if tag_name:
                                                movie_genre_names.update(
                                                    self._extract_metadata_from_string(
                                                        tag_name, is_genre=True
                                                    )
                                                )
                                                movie_region_names.update(
                                                    self._extract_metadata_from_string(
                                                        tag_name, is_genre=False
                                                    )
                                                )
                            except json.JSONDecodeError as e:
                                logger.warning(
                                    f"Failed to parse raw_data for douban_id {douban_id}: {e}"
                                )

                        # Build movie dictionary
                        movie = {
                            "id": int(douban_id),
                            "title": title or "",
                            "year": year,
                            "rating": rating,
                            "rating_count": rating_count,
                            "type": item_type,
                            "genre_ids": [genre_map[gn] for gn in movie_genre_names],
                            "region_ids": [region_map[rn] for rn in movie_region_names],
                            "posters": list(poster_urls),
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

            # Post-import optimization
            self._optimize_db(temp_db_path)

            # Atomic swap
            logger.info(f"Swapping {temp_db_path} to {target_db_path}")

            # Dispose existing connections to ensure they stop using the old file handles
            database.engine.dispose()

            # Remove associated SQLite sidecars if they exist for the target
            for suffix in ["-wal", "-shm"]:
                sidecar = target_db_path.with_name(target_db_path.name + suffix)
                if sidecar.exists():
                    try:
                        sidecar.unlink()
                    except Exception as e:
                        logger.warning(f"Could not remove sidecar {sidecar}: {e}")

            if target_db_path.exists():
                # On Linux we can rename over an existing file
                shutil.move(temp_db_path, target_db_path)
            else:
                shutil.move(temp_db_path, target_db_path)

            # Clear application cache after successful swap
            cache_manager.clear()

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
            if temp_db_path.exists():
                with contextlib.suppress(Exception):
                    temp_db_path.unlink()
            with self._lock:
                self._status.status = "failed"
                self._status.message = str(e)
                self._status.completed_at = datetime.now()

    def _insert_batch(self, db: Session, movies: list[dict]) -> None:
        """Insert a batch of movies and their associations."""
        try:
            for movie_data in movies:
                genre_ids = movie_data.pop("genre_ids", [])
                region_ids = movie_data.pop("region_ids", [])
                posters = movie_data.pop("posters", [])

                movie = Movie(**movie_data)
                db.add(movie)
                db.flush()

                for gid in genre_ids:
                    db.add(MovieGenre(movie_id=movie.id, genre_id=gid))

                for rid in region_ids:
                    db.add(MovieRegion(movie_id=movie.id, region_id=rid))

                for poster_url in posters:
                    db.add(MoviePoster(movie_id=movie.id, url=poster_url))

            db.flush()
            db.expunge_all()
        except Exception as e:
            logger.exception(f"Failed to insert batch: {e}")
            raise

    def _optimize_db(self, db_path: Path) -> None:
        """Run post-import optimizations."""
        logger.info("Running post-import optimizations...")
        # Use isolation_level=None for autocommit mode, required for VACUUM
        conn = sqlite3.connect(db_path, isolation_level=None)
        try:
            cursor = conn.cursor()

            # Create FTS5 table
            logger.info("Creating FTS5 virtual table for search...")
            cursor.execute(f"DROP TABLE IF EXISTS {FTS_TABLE_NAME}")
            cursor.execute(FTS_CREATE_TABLE_SQL)
            cursor.execute(FTS_INSERT_ALL_SQL)

            # ANALYZE for query planner
            logger.info("Running ANALYZE...")
            cursor.execute("ANALYZE")

            # VACUUM to shrink and defragment
            logger.info("Running VACUUM...")
            cursor.execute("VACUUM")

            conn.commit()
            logger.info("Optimizations complete")
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            # Don't re-raise, we still want the DB to be usable even if not perfectly optimized
        finally:
            conn.close()


import_service = ImportService()

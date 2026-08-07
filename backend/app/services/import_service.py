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
from sqlalchemy.engine import Engine
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
)
from app.metadata_constants import VALID_GENRES, VALID_REGIONS
from app.schemas import ImportStatus

# Configure logger
logger = logging.getLogger("douban.import")

_SOURCE_ROW_SQL = (
    "SELECT douban_id, imdb_id, douban_title, year, rating, raw_data, type, update_time FROM item"
)


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

    _BATCH_SIZE = 1000
    _MAX_ERROR_LOGS = 10

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

    def start_import(self, source_path: str, force_full: bool = False) -> ImportStatus:
        """Start the import process in a background thread.

        Args:
            source_path: Path to the source SQLite database.
            force_full: When True, rebuild the target database from scratch instead
                of performing an incremental merge. A full rebuild is also used
                implicitly when the target database does not exist yet.
        """
        with self._lock:
            if self._status.status == "running":
                logger.warning("Import already in progress, cannot start new import")
                raise RuntimeError("Import already in progress")

            logger.info(f"Starting import from: {source_path} (force_full={force_full})")
            self._status = ImportStatus(
                status="running",
                processed=0,
                total=0,
                percentage=0.0,
                started_at=datetime.now(),
            )

            thread = threading.Thread(target=self._import_data, args=(source_path, force_full))
            thread.daemon = True
            thread.start()

            return self._status

    def _extract_metadata_from_string(self, s: str, is_genre: bool = True) -> set[str]:
        """Extract valid genres or regions from a string using greedy matching."""
        if not s:
            return set()

        found = set()
        # Split by major delimiters into segments.
        # Do not treat parentheses or other braces as delimiters.
        segments = re.split(r"[/|\\,，、]", s)  # noqa: RUF001

        whitelist = self._SORTED_GENRES if is_genre else self._SORTED_REGIONS
        valid_set = self.VALID_GENRES if is_genre else self.VALID_REGIONS

        for seg in segments:
            cleaned_seg = seg.strip()
            if not cleaned_seg:
                continue

            # First try matching the entire segment
            if cleaned_seg in valid_set:
                found.add(cleaned_seg)
                continue

            # If no whole match, find all whitelist items present in the segment
            for item in whitelist:
                if not item:
                    continue

                # Use word boundaries to avoid partial matches (e.g., "金" in "金像奖")
                pattern = rf"\b{re.escape(item)}\b"
                if re.search(pattern, cleaned_seg):
                    found.add(item)

        return found

    def _build_movie_dict(  # noqa: PLR0912
        self,
        row: tuple,
        genre_map: dict[str, int],
        region_map: dict[str, int],
    ) -> dict:
        """Build a movie dictionary (with associations) from a source item row."""
        douban_id, _, title, year, rating, raw_data, item_type, update_time = row

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
                                self._extract_metadata_from_string(r, is_genre=False)
                            )

                    # Extract genres
                    genres_list = detail.get("genres", [])
                    types_list = detail.get("types", [])
                    # Handle both "genres" and "types" as lists
                    for g in (genres_list if isinstance(genres_list, list) else []) + (
                        types_list if isinstance(types_list, list) else []
                    ):
                        if isinstance(g, str):
                            movie_genre_names.update(
                                self._extract_metadata_from_string(g, is_genre=True)
                            )

                    # Extract from card_subtitle or subtitle
                    card_subtitle = detail.get("card_subtitle") or detail.get("subtitle", "")
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
                                tokens = self._extract_metadata_from_string(parts[i], is_genre=True)
                                if tokens:
                                    genre_idx = i
                                    break

                            if genre_idx != -1:
                                # Parts before the first genre are regions
                                for i in range(start_idx, genre_idx):
                                    movie_region_names.update(
                                        self._extract_metadata_from_string(parts[i], is_genre=False)
                                    )
                            elif len(parts) > start_idx:
                                # Fallback if no genre found
                                movie_region_names.update(
                                    self._extract_metadata_from_string(
                                        parts[start_idx], is_genre=False
                                    )
                                )
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse raw_data for douban_id {douban_id}: {e}")

        # Build movie dictionary
        return {
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

    def _import_data(self, source_path: str, force_full: bool = False) -> None:
        """Internal method to perform the import."""
        target_db_path = Path(database.get_db_path())
        temp_db_path = target_db_path.with_suffix(target_db_path.suffix + ".tmp")
        source_conn: sqlite3.Connection | None = None
        try:
            logger.info(f"Connecting to source database: {source_path}")
            if not Path(source_path).exists():
                raise FileNotFoundError(f"Source file not found: {source_path}")

            # Connect to source database (read-only + immutable for WAL-mode compatibility)
            # immutable=1 tells SQLite not to create auxiliary files (-wal, -shm)
            source_conn = sqlite3.connect(f"file:{source_path}?mode=ro&immutable=1", uri=True)

            # Ensure data directory exists
            temp_db_path.parent.mkdir(parents=True, exist_ok=True)
            if temp_db_path.exists():
                temp_db_path.unlink()

            if force_full or not target_db_path.exists():
                logger.info("Running full rebuild import")
                self._import_full(source_path, source_conn, temp_db_path)
            else:
                logger.info("Running incremental import")
                self._import_incremental(source_path, source_conn, temp_db_path)

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

            shutil.move(temp_db_path, target_db_path)

            # Clear application cache after successful swap
            cache_manager.clear()

            logger.info(f"Import completed successfully for {target_db_path}")
            with self._lock:
                self._status.status = "completed"
                self._status.percentage = 100.0
                self._status.completed_at = datetime.now()

        except Exception as e:
            logger.exception(f"Import failed: {e}")
            if temp_db_path.exists():
                with contextlib.suppress(Exception):
                    temp_db_path.unlink()
            if source_conn is not None:
                with contextlib.suppress(Exception):
                    source_conn.close()
            with self._lock:
                self._status.status = "failed"
                self._status.message = str(e)
                self._status.completed_at = datetime.now()

    def _import_full(
        self, source_path: str, source_conn: sqlite3.Connection, temp_db_path: Path
    ) -> None:
        """Full rebuild: fresh empty temp DB, import every source row."""
        source_cursor = source_conn.cursor()
        source_cursor.execute(f"{_SOURCE_ROW_SQL} WHERE type IN ('movie', 'tv')")

        temp_engine = self._open_temp_engine(temp_db_path, fresh=True)

        with Session(temp_engine) as db:
            logger.info("Populating genres and regions...")
            genre_map, region_map = self._seed_metadata(db)

            processed = 0
            batch: list[dict] = []
            error_count = 0
            for row in source_cursor:
                douban_id = None
                try:
                    douban_id = row[0]
                    batch.append(self._build_movie_dict(row, genre_map, region_map))
                    if len(batch) >= self._BATCH_SIZE:
                        self._insert_batch(db, batch)
                        processed += len(batch)
                        batch = []
                        self._update_progress(processed, processed)
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing row {douban_id}: {e}", exc_info=True)
                    if error_count > self._MAX_ERROR_LOGS:
                        logger.warning(
                            f"Suppressing detailed error logs after {error_count} errors"
                        )

            if batch:
                logger.info(f"Inserting final batch of {len(batch)} records...")
                self._insert_batch(db, batch)
                processed += len(batch)

            db.commit()
            with self._lock:
                self._status.processed = processed
                self._status.total = processed
                self._status.percentage = 100.0

        # Release the temp file so the standalone VACUUM connection can lock it
        temp_engine.dispose()
        logger.info(f"Full import processed {processed} records with {error_count} errors")

    def _import_incremental(  # noqa: PLR0915
        self, source_path: str, source_conn: sqlite3.Connection, temp_db_path: Path
    ) -> None:
        """Incremental merge: copy the existing target, apply only changed rows.

        Only source rows whose type or update_time changed (or that are new) are
        re-parsed and merged; rows missing from the source are deleted so the
        target mirrors the source. Python memory stays O(1): the delta is computed
        with set-based SQL via ATTACH instead of an in-memory snapshot.
        """
        # Copy the existing target so the serving DB keeps serving immutable reads
        shutil.copy2(database.get_db_path(), temp_db_path)

        temp_engine = self._open_temp_engine(temp_db_path, fresh=False)

        # Set-based delta detection and deletion on the copy
        with temp_engine.begin() as conn:
            conn.execute(text("PRAGMA foreign_keys = ON"))
            escaped = source_path.replace("'", "''")
            conn.execute(text(f"ATTACH DATABASE '{escaped}' AS src"))
            conn.execute(
                text(
                    "CREATE TEMP TABLE tmp_src AS "
                    "SELECT douban_id AS id, type AS typ, "
                    "CAST(update_time AS INT) AS upd "
                    "FROM src.item WHERE type IN ('movie', 'tv')"
                )
            )
            changed_rows = conn.execute(
                text(
                    "SELECT t.id FROM tmp_src t "
                    "LEFT JOIN movies m ON m.id = t.id "
                    "WHERE m.id IS NULL OR m.type <> t.typ "
                    "OR NOT (m.updated_at IS t.upd)"
                )
            ).fetchall()
            change_ids = [int(r[0]) for r in changed_rows]

            # Delete rows that no longer exist in the source (mirror source DB).
            # Children are removed explicitly so we do not depend on the
            # foreign_keys pragma for cascading.
            for table in ["movie_posters", "movie_regions", "movie_genres"]:
                conn.execute(
                    text(f"DELETE FROM {table} WHERE movie_id NOT IN (SELECT id FROM tmp_src)")
                )
            conn.execute(text("DELETE FROM movies WHERE id NOT IN (SELECT id FROM tmp_src)"))
            conn.execute(text("DETACH DATABASE src"))

        with self._lock:
            self._status.total = len(change_ids)

        if not change_ids:
            logger.info("No changed records to import, nothing to update")
            with self._lock:
                self._status.processed = 0
                self._status.percentage = 100.0
            # Release the temp file before the standalone VACUUM connection opens
            temp_engine.dispose()
            return

        # Fetch and merge only the changed rows
        with Session(temp_engine) as db:
            # Ensure genres/regions exist (a freshly created target may be empty)
            genre_map, region_map = self._ensure_metadata(db)
            batch: list[dict] = []
            error_count = 0
            processed = 0
            for douban_id in change_ids:
                row = source_conn.execute(
                    f"{_SOURCE_ROW_SQL} WHERE douban_id = ?", (str(douban_id),)
                ).fetchone()
                if row is None:
                    continue
                try:
                    batch.append(self._build_movie_dict(row, genre_map, region_map))
                    if len(batch) >= self._BATCH_SIZE:
                        self._merge_batch(db, batch)
                        processed += len(batch)
                        batch = []
                        self._update_progress(processed, len(change_ids))
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing row {douban_id}: {e}", exc_info=True)
                    if error_count > self._MAX_ERROR_LOGS:
                        logger.warning(
                            f"Suppressing detailed error logs after {error_count} errors"
                        )

            if batch:
                logger.info(f"Merging final batch of {len(batch)} records...")
                self._merge_batch(db, batch)
                processed += len(batch)

            db.commit()
            with self._lock:
                self._status.processed = processed
                self._status.total = len(change_ids)
                self._status.percentage = 100.0

        # Release the temp file so the standalone VACUUM connection can lock it
        temp_engine.dispose()
        logger.info(f"Incremental import merged {processed} records with {error_count} errors")

    def _open_temp_engine(self, temp_db_path: Path, fresh: bool) -> Engine:
        """Create a writable engine on the temp DB with import-friendly pragmas."""
        temp_engine = create_engine(
            f"sqlite:///{temp_db_path}",
            connect_args={"check_same_thread": False},
        )
        with temp_engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode = DELETE"))
            conn.execute(text("PRAGMA synchronous = OFF"))
            conn.execute(text("PRAGMA cache_size = -100000"))
            if fresh:
                Base.metadata.create_all(bind=temp_engine)  # type: ignore[attr-defined]
        return temp_engine

    def _seed_metadata(self, db: Session) -> tuple[dict[str, int], dict[str, int]]:
        """Pre-populate genres/regions in a freshly built DB and return name->id maps."""
        for g_name in sorted(self.VALID_GENRES):
            db.add(Genre(name=g_name))
        db.flush()
        for r_name in sorted(self.VALID_REGIONS):
            db.add(Region(name=r_name))
        db.flush()
        db.commit()
        genre_map = {g.name: g.id for g in db.query(Genre).all()}
        region_map = {r.name: r.id for r in db.query(Region).all()}
        return genre_map, region_map

    def _load_metadata_maps(self, db: Session) -> tuple[dict[str, int], dict[str, int]]:
        """Load existing genre and region name->id maps from the target DB."""
        genre_map = {g.name: g.id for g in db.query(Genre).all()}
        region_map = {r.name: r.id for r in db.query(Region).all()}
        return genre_map, region_map

    def _ensure_metadata(self, db: Session) -> tuple[dict[str, int], dict[str, int]]:
        """Seed any missing genres/regions and return name->id maps."""
        existing_genres = {g.name for g in db.query(Genre).all()}
        for name in sorted(self.VALID_GENRES):
            if name not in existing_genres:
                db.add(Genre(name=name))
        existing_regions = {r.name for r in db.query(Region).all()}
        for name in sorted(self.VALID_REGIONS):
            if name not in existing_regions:
                db.add(Region(name=name))
        db.flush()
        return self._load_metadata_maps(db)

    def _add_associations(
        self,
        db: Session,
        movie_id: int,
        genre_ids: list[int],
        region_ids: list[int],
        posters: list[str],
    ) -> None:
        """Add the genre/region/poster associations for a movie."""
        for gid in genre_ids:
            db.add(MovieGenre(movie_id=movie_id, genre_id=gid))
        for rid in region_ids:
            db.add(MovieRegion(movie_id=movie_id, region_id=rid))
        for poster_url in posters:
            db.add(MoviePoster(movie_id=movie_id, url=poster_url))

    def _insert_batch(self, db: Session, movies: list[dict]) -> None:
        """Insert a batch of new movies and their associations."""
        try:
            for movie_data in movies:
                genre_ids = movie_data.pop("genre_ids", [])
                region_ids = movie_data.pop("region_ids", [])
                posters = movie_data.pop("posters", [])

                movie = Movie(**movie_data)
                db.add(movie)
                db.flush()
                self._add_associations(db, movie_data["id"], genre_ids, region_ids, posters)

            db.flush()
            db.expunge_all()
        except Exception as e:
            logger.exception(f"Failed to insert batch: {e}")
            raise

    def _merge_batch(self, db: Session, movies: list[dict]) -> None:
        """Upsert a batch of movies and their associations."""
        try:
            for movie_data in movies:
                genre_ids = movie_data.pop("genre_ids", [])
                region_ids = movie_data.pop("region_ids", [])
                posters = movie_data.pop("posters", [])

                movie_id = movie_data["id"]
                movie = db.get(Movie, movie_id)
                if movie is None:
                    movie = Movie(**movie_data)
                    db.add(movie)
                    db.flush()
                else:
                    for key, value in movie_data.items():
                        setattr(movie, key, value)
                    db.query(MovieGenre).filter(MovieGenre.movie_id == movie_id).delete()
                    db.query(MovieRegion).filter(MovieRegion.movie_id == movie_id).delete()
                    db.query(MoviePoster).filter(MoviePoster.movie_id == movie_id).delete()

                self._add_associations(db, movie_id, genre_ids, region_ids, posters)

            db.flush()
            db.expunge_all()
        except Exception as e:
            logger.exception(f"Failed to merge batch: {e}")
            raise

    def _update_progress(self, processed: int, total: int) -> None:
        """Update import status progress."""
        with self._lock:
            self._status.processed = processed
            self._status.total = total
            self._status.percentage = (processed / total * 100) if total > 0 else 100.0

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

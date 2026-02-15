"""Database models and connection management."""

import contextlib
import sqlite3
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    create_engine,
    event,
)
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

from app.config import settings

Base = declarative_base()


# FTS5 Search Constants
FTS_TABLE_NAME = "movie_search"
# Use 'trigram' tokenizer to support arbitrary substring search (including CJK)
# Requires SQLite 3.34.0+
FTS_CREATE_TABLE_SQL = (
    f"CREATE VIRTUAL TABLE {FTS_TABLE_NAME} USING "
    "fts5(title, content='movies', content_rowid='id', tokenize='trigram')"
)
FTS_INSERT_ALL_SQL = f"INSERT INTO {FTS_TABLE_NAME}(rowid, title) SELECT id, title FROM movies"


class Movie(Base):  # type: ignore[misc, valid-type]
    """Movie model representing a Douban movie or TV show."""

    __tablename__ = "movies"

    id = Column(Integer, primary_key=True)
    title = Column(String(256), nullable=False)
    year = Column(Integer, nullable=True, index=True)
    rating = Column(Float, nullable=True, index=True)
    rating_count = Column(Integer, default=0, index=True)
    type = Column(String(16), nullable=False, index=True)
    updated_at = Column(Integer, nullable=True)

    genres = relationship("MovieGenre", back_populates="movie", cascade="all, delete-orphan")  # type: ignore[var-annotated]
    regions = relationship("MovieRegion", back_populates="movie", cascade="all, delete-orphan")  # type: ignore[var-annotated]
    posters = relationship("MoviePoster", back_populates="movie", cascade="all, delete-orphan")  # type: ignore[var-annotated]

    __table_args__ = (
        Index("ix_movies_rating_id", "rating", "id"),
        Index("ix_movies_year_id", "year", "id"),
        Index("ix_movies_rating_count_id", "rating_count", "id"),
    )


class Genre(Base):  # type: ignore[misc, valid-type]
    """Genre model."""

    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(32), unique=True, nullable=False, index=True)

    movie_associations = relationship("MovieGenre", back_populates="genre_obj")  # type: ignore[var-annotated]


class MovieGenre(Base):  # type: ignore[misc, valid-type]
    """Genre association model for movies."""

    __tablename__ = "movie_genres"

    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True)
    genre_id = Column(Integer, ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True)

    movie = relationship("Movie", back_populates="genres")  # type: ignore[var-annotated]
    genre_obj = relationship("Genre", back_populates="movie_associations")  # type: ignore[var-annotated]


class Region(Base):  # type: ignore[misc, valid-type]
    """Region model."""

    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(32), unique=True, nullable=False, index=True)

    movie_associations = relationship("MovieRegion", back_populates="region_obj")  # type: ignore[var-annotated]


class MovieRegion(Base):  # type: ignore[misc, valid-type]
    """Region association model for movies."""

    __tablename__ = "movie_regions"

    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True)
    region_id = Column(Integer, ForeignKey("regions.id", ondelete="CASCADE"), primary_key=True)

    movie = relationship("Movie", back_populates="regions")  # type: ignore[var-annotated]
    region_obj = relationship("Region", back_populates="movie_associations")  # type: ignore[var-annotated]


class MoviePoster(Base):  # type: ignore[misc, valid-type]
    """Poster URL model for movies."""

    __tablename__ = "movie_posters"

    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True)
    url = Column(String(512), primary_key=True)

    movie = relationship("Movie", back_populates="posters")  # type: ignore[var-annotated]


DATABASE_NAME = "movies.db"


def get_db_path() -> str:
    """Get the path to the SQLite database file."""
    # If DATABASE_URL is already defined in this module (e.g. by tests), use it
    if "DATABASE_URL" in globals():
        url = globals()["DATABASE_URL"]
        if isinstance(url, str) and url.startswith("sqlite:///"):
            return url.replace("sqlite:///", "").split("?")[0]

    return str(Path(settings.data_dir).absolute() / "db" / DATABASE_NAME)


# Construct initial DATABASE_URL
# Always read-only for the production serving engine to ensure data integrity
# and allow safe atomic swaps.
DATABASE_URL = f"sqlite:///{get_db_path()}?mode=ro"


def sqlite_creator() -> sqlite3.Connection:
    """Custom creator to ensure URI mode and proper read-only handling."""
    # We use URI mode to allow mode=ro, which prevents 0-byte file creation.
    # The path must be absolute for the 'file:' URI prefix to work reliably.
    path = get_db_path()
    # If the database is read-only and doesn't exist, we don't even try to connect
    # to avoid 0-byte file creation or confusing error messages.
    if "mode=ro" in DATABASE_URL and not Path(path).exists():
        raise sqlite3.OperationalError(f"Database file not found at {path}")

    # Use URI mode explicitly
    return sqlite3.connect(
        f"file:{path}?mode=ro" if "mode=ro" in DATABASE_URL else path,
        uri=True,
        check_same_thread=False,
    )


engine = create_engine(
    "sqlite://",  # Generic sqlite URL, actual connection handled by creator
    creator=sqlite_creator,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):  # type: ignore[no-untyped-def]
    """Enable high-performance pragmas for SQLite."""
    # If the connection is read-only and the file is missing,
    # some drivers might still create a 0-byte file.
    # However, with uri=True and mode=ro, it should generally fail.
    cursor = dbapi_connection.cursor()

    # We disable WAL for the database because we use atomic swaps
    # and serve it read-only. WAL is only useful for concurrent writes.
    # It also creates sidecar files (-wal, -shm) that complicate atomic swaps.
    if "mode=ro" in DATABASE_URL:
        with contextlib.suppress(sqlite3.OperationalError):
            cursor.execute("PRAGMA journal_mode=DELETE")
    else:
        # For writeable databases, we still prefer DELETE or TRUNCATE
        # to avoid sidecar files interfering with the import swap logic.
        with contextlib.suppress(sqlite3.OperationalError):
            cursor.execute("PRAGMA journal_mode=TRUNCATE")

    cursor.execute("PRAGMA synchronous=NORMAL")

    # Increase cache size (e.g., 100MB)
    cursor.execute("PRAGMA cache_size=-100000")
    # Enable memory-mapped I/O (e.g., up to 1GB)
    cursor.execute("PRAGMA mmap_size=1000000000")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Generate database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

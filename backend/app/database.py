"""Database models and connection management."""

import os
from collections.abc import Generator

from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    event,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker

Base = declarative_base()


class Movie(Base):  # type: ignore[misc, valid-type]
    """Movie model representing a Douban movie or TV show."""

    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    douban_id = Column(String(16), unique=True, nullable=False, index=True)
    imdb_id = Column(String(16), nullable=True)
    title = Column(String(256), nullable=False)
    year = Column(Integer, nullable=True, index=True)
    rating = Column(Float, nullable=True, index=True)
    rating_count = Column(Integer, default=0, index=True)
    type = Column(String(16), nullable=False, index=True)
    poster_url = Column(Text, nullable=True)
    douban_url = Column(Text, nullable=False)
    updated_at = Column(Integer, nullable=True)

    genres = relationship("MovieGenre", back_populates="movie", cascade="all, delete-orphan")  # type: ignore[var-annotated]


class MovieGenre(Base):  # type: ignore[misc, valid-type]
    """Genre association model for movies."""

    __tablename__ = "movie_genres"

    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True)
    genre = Column(String(32), primary_key=True, index=True)

    movie = relationship("Movie", back_populates="genres")  # type: ignore[var-annotated]


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/movies.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30,
    }
    if DATABASE_URL.startswith("sqlite")
    else {},
    pool_pre_ping=True,
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):  # type: ignore[no-untyped-def]
    """Enable WAL mode for SQLite."""
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)  # type: ignore[attr-defined]


def get_db() -> Generator[Session, None, None]:
    """Generate database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

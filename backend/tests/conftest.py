"""Pytest configuration and fixtures."""

import os
import sqlite3
import tempfile
from typing import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app import database as app_database
from app.database import Base, Movie, MovieGenre, get_db
from app.main import app
from app.services import import_service as app_import_service
from app.services.import_service import ImportService


@pytest.fixture(scope="session")
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture(scope="session")
def temp_data_dir(temp_dir: str) -> str:
    """Create temp data directory."""
    data_dir = os.path.join(temp_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


@pytest.fixture(scope="session")
def temp_import_dir(temp_dir: str) -> str:
    """Create temp import directory."""
    import_dir = os.path.join(temp_dir, "import")
    os.makedirs(import_dir, exist_ok=True)
    return import_dir


@pytest.fixture(scope="session")
def temp_db_path(temp_data_dir: str) -> str:
    """Get path to temporary database."""
    return os.path.join(temp_data_dir, "test_movies.db")


@pytest.fixture(scope="session")
def temp_source_db_path(temp_import_dir: str) -> str:
    """Get path to temporary source database."""
    return os.path.join(temp_import_dir, "source_backup.sqlite3")


@pytest.fixture(scope="session")
def source_db_connection(temp_source_db_path: str) -> Generator[sqlite3.Connection, None, None]:
    """Create and populate a source SQLite database for import testing."""
    conn = sqlite3.connect(temp_source_db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS item (
            douban_id TEXT PRIMARY KEY,
            imdb_id TEXT,
            douban_title TEXT,
            year INTEGER,
            rating REAL,
            raw_data TEXT,
            type TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_type ON item (type)")
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def populated_source_db(source_db_connection: sqlite3.Connection) -> sqlite3.Connection:
    """Populate source database with test data."""
    cursor = source_db_connection.cursor()

    test_movies = [
        (
            "1001",
            "tt1001",
            "Test Movie 1",
            2000,
            8.5,
            '{"detail": {"rating": {"count": 1000}, "pic": {"normal": "http://example.com/p1.jpg"}, "card_subtitle": "2000 / 美国 / 剧情 犯罪"}}',
            "movie",
        ),
        (
            "1002",
            "tt1002",
            "Test Movie 2",
            2001,
            7.5,
            '{"detail": {"rating": {"count": 500}, "pic": {"large": "http://example.com/p2.jpg"}, "card_subtitle": "2001 / 美国 / 喜剧"}}',
            "movie",
        ),
        (
            "1003",
            "tt1003",
            "Test TV Show 1",
            2010,
            9.0,
            '{"detail": {"rating": {"count": 2000}, "card_subtitle": "2010 / 美国 / 剧情 悬疑"}}',
            "tv",
        ),
        (
            "1004",
            "tt1004",
            "Test Movie No Rating",
            2015,
            None,
            '{"detail": {"card_subtitle": "2015 / 美国 / 科幻"}}',
            "movie",
        ),
        (
            "1002",
            "tt1002",
            "Test Movie 2",
            2001,
            7.5,
            '{"detail": {"rating": {"count": 500}, "pic": {"large": "http://example.com/p2.jpg"}, "card_subtitle": "2001 / 喜剧"}}',
            "movie",
        ),
        (
            "1003",
            "tt1003",
            "Test TV Show 1",
            2010,
            9.0,
            '{"detail": {"rating": {"count": 2000}, "card_subtitle": "2010 / 剧情 悬疑"}}',
            "tv",
        ),
        (
            "1004",
            "tt1004",
            "Test Movie No Rating",
            2015,
            None,
            '{"detail": {"card_subtitle": "2015 / 美国 / 科幻"}}',
            "movie",
        ),
        (
            "1005",
            "tt1005",
            "Test Movie No Genres",
            2020,
            6.0,
            "{}",
            "movie",
        ),
        (
            "1300613",
            "tt0107048",
            "土拨鼠之日",
            1993,
            8.6,
            '{"detail": {"rating": {"count": 237672}, "cover_url": "https://example.com/cover.jpg", "card_subtitle": "1993 / 美国 / 剧情 喜剧 爱情 奇幻"}}',
            "movie",
        ),
    ]

    cursor.executemany(
        "INSERT OR REPLACE INTO item (douban_id, imdb_id, douban_title, year, rating, raw_data, type) VALUES (?, ?, ?, ?, ?, ?, ?)",
        test_movies,
    )
    source_db_connection.commit()
    return source_db_connection


@pytest.fixture
def test_engine(temp_db_path: str):
    """Create test database engine."""
    engine = create_engine(
        f"sqlite:///{temp_db_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create test database session."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(test_engine, db_session: Session) -> Generator[TestClient, None, None]:
    """Create test client with database override."""
    original_engine = app_database.engine
    original_sessionmaker = app_database.SessionLocal

    app_database.engine = test_engine
    app_database.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    app_import_service.engine = test_engine

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    app_database.engine = original_engine
    app_database.SessionLocal = original_sessionmaker
    app_import_service.engine = original_engine


@pytest.fixture(autouse=True)
def reset_import_service_singleton():
    """Reset the ImportService singleton before each test."""
    ImportService._instance = None
    yield
    ImportService._instance = None


@pytest.fixture
def sample_movies(db_session: Session) -> list[Movie]:
    """Create sample movies in the test database."""
    movies = [
        Movie(
            douban_id="2001",
            imdb_id="tt2001",
            title="Drama Movie",
            year=2000,
            rating=8.0,
            rating_count=1000,
            type="movie",
            poster_url="http://example.com/p1.jpg",
            douban_url="https://movie.douban.com/subject/2001/",
        ),
        Movie(
            douban_id="2002",
            imdb_id="tt2002",
            title="Comedy Movie",
            year=2001,
            rating=7.0,
            rating_count=500,
            type="movie",
            poster_url="http://example.com/p2.jpg",
            douban_url="https://movie.douban.com/subject/2002/",
        ),
        Movie(
            douban_id="2003",
            imdb_id="tt2003",
            title="Action Movie",
            year=2002,
            rating=8.5,
            rating_count=2000,
            type="movie",
            poster_url="http://example.com/p3.jpg",
            douban_url="https://movie.douban.com/subject/2003/",
        ),
        Movie(
            douban_id="3001",
            imdb_id="tt3001",
            title="TV Show One",
            year=2010,
            rating=9.0,
            rating_count=3000,
            type="tv",
            poster_url="http://example.com/p4.jpg",
            douban_url="https://movie.douban.com/subject/3001/",
        ),
        Movie(
            douban_id="3002",
            imdb_id="tt3002",
            title="TV Show Two",
            year=2011,
            rating=7.5,
            rating_count=1500,
            type="tv",
            poster_url="http://example.com/p5.jpg",
            douban_url="https://movie.douban.com/subject/3002/",
        ),
        Movie(
            douban_id="4001",
            imdb_id=None,
            title="Unrated Movie",
            year=2020,
            rating=None,
            rating_count=0,
            type="movie",
            poster_url=None,
            douban_url="https://movie.douban.com/subject/4001/",
        ),
    ]
    for movie in movies:
        db_session.add(movie)
    db_session.commit()

    for i, movie in enumerate(movies):
        db_session.refresh(movie)

    return movies


@pytest.fixture
def movies_with_genres(db_session: Session, sample_movies: list[Movie]) -> list[Movie]:
    """Add genres to sample movies."""
    genres_data = [
        (sample_movies[0].id, "剧情"),
        (sample_movies[0].id, "犯罪"),
        (sample_movies[1].id, "喜剧"),
        (sample_movies[2].id, "动作"),
        (sample_movies[2].id, "犯罪"),
        (sample_movies[3].id, "剧情"),
        (sample_movies[3].id, "悬疑"),
        (sample_movies[4].id, "喜剧"),
    ]
    for movie_id, genre in genres_data:
        db_session.add(MovieGenre(movie_id=movie_id, genre=genre))
    db_session.commit()
    return sample_movies

"""Pytest configuration and fixtures."""

import sqlite3
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app import database as app_database
from app.database import Base, Genre, Movie, MovieGenre, get_db
from app.main import app
from app.services.import_service import ImportService


@pytest.fixture(scope="session")
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture(scope="session")
def temp_data_dir(temp_dir: str) -> str:
    """Create temp data directory."""
    data_dir = Path(temp_dir) / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir)


@pytest.fixture(scope="session")
def temp_import_dir(temp_dir: str) -> str:
    """Create temp import directory."""
    import_dir = Path(temp_dir) / "import"
    import_dir.mkdir(parents=True, exist_ok=True)
    return str(import_dir)


@pytest.fixture
def temp_db_path(temp_data_dir: str, request: pytest.FixtureRequest) -> str:
    """Get path to unique temporary database for each test."""
    test_id = request.node.nodeid.replace("/", "_").replace(":", "_")
    db_path = Path(temp_data_dir) / f"test_{test_id}.db"
    return str(db_path)


@pytest.fixture(scope="session")
def temp_source_db_path(temp_import_dir: str) -> str:
    """Get path to temporary source database."""
    return str(Path(temp_import_dir) / "source_backup.sqlite3")


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
            type TEXT,
            update_time REAL
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
            '{"detail": {"rating": {"count": 1000}, '
            '"pic": {"normal": "http://example.com/p1.jpg"}, '
            '"card_subtitle": "2000 / 美国 / 剧情 犯罪"}}',
            "movie",
            1612985849.0,
        ),
        (
            "1002",
            "tt1002",
            "Test Movie 2",
            2001,
            7.5,
            '{"detail": {"rating": {"count": 500}, '
            '"pic": {"large": "http://example.com/p2.jpg"}, '
            '"card_subtitle": "2001 / 美国 / 喜剧"}}',
            "movie",
            1612985849.0,
        ),
        (
            "1003",
            "tt1003",
            "Test TV Show 1",
            2010,
            9.0,
            '{"detail": {"rating": {"count": 2000}, "card_subtitle": "2010 / 美国 / 剧情 悬疑"}}',
            "tv",
            1612985849.0,
        ),
        (
            "1004",
            "tt1004",
            "Test Movie No Rating",
            2015,
            None,
            '{"detail": {"card_subtitle": "2015 / 美国 / 科幻"}}',
            "movie",
            1612985849.0,
        ),
        (
            "1005",
            "tt1005",
            "Test Movie No Genres",
            2020,
            6.0,
            "{}",
            "movie",
            1612985849.0,
        ),
        (
            "1300613",
            "tt0107048",
            "土拨鼠之日",
            1993,
            8.6,
            '{"detail": {"rating": {"count": 237672}, '
            '"cover_url": "https://example.com/cover.jpg", '
            '"card_subtitle": "1993 / 美国 / 剧情 喜剧 爱情 奇幻"}}',
            "movie",
            1612985849.0,
        ),
        (
            "1449961",
            "tt0365559",
            "涅槃纽约不插电演唱会",
            1993,
            9.7,
            '{"detail": {"rating": {"count": 10308}, '
            '"subtitle": "1993 / 美国 / 纪录片 音乐 / Beth McCarthy-Miller", '
            '"photos": ["https://example.com/photo1.jpg", "https://example.com/photo2.jpg"]}}',
            "movie",
            1612985849.0,
        ),
        (
            "9999",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ),
        (
            "9998",
            None,
            "Book Item",
            2020,
            None,
            "{}",
            "book",
            1612985849.0,
        ),
    ]

    cursor.executemany(
        "INSERT OR REPLACE INTO item "
        "(douban_id, imdb_id, douban_title, year, rating, raw_data, type, update_time) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
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
        poolclass=NullPool,
    )
    Base.metadata.create_all(bind=engine)

    # Create FTS5 table for tests
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE VIRTUAL TABLE movie_search USING "
                "fts5(title, content='movies', content_rowid='id')"
            )
        )

    yield engine

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create test database session."""
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(
    test_engine, db_session: Session, temp_db_path: str
) -> Generator[TestClient, None, None]:
    """Create test client with database override."""
    original_engine = app_database.engine
    original_session_factory = app_database.SessionLocal
    original_db_url = app_database.DATABASE_URL

    app_database.engine = test_engine
    app_database.DATABASE_URL = f"sqlite:///{temp_db_path}"
    app_database.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

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
    app_database.DATABASE_URL = original_db_url
    app_database.SessionLocal = original_session_factory


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
            id=2001,
            title="Drama Movie",
            year=2000,
            rating=8.0,
            rating_count=1000,
            type="movie",
        ),
        Movie(
            id=2002,
            title="Comedy Movie",
            year=2001,
            rating=7.0,
            rating_count=500,
            type="movie",
        ),
        Movie(
            id=2003,
            title="Action Movie",
            year=2002,
            rating=8.5,
            rating_count=2000,
            type="movie",
        ),
        Movie(
            id=3001,
            title="TV Show One",
            year=2010,
            rating=9.0,
            rating_count=3000,
            type="tv",
        ),
        Movie(
            id=3002,
            title="TV Show Two",
            year=2011,
            rating=7.5,
            rating_count=1500,
            type="tv",
        ),
        Movie(
            id=4001,
            title="Unrated Movie",
            year=2020,
            rating=None,
            rating_count=0,
            type="movie",
        ),
    ]
    for movie in movies:
        db_session.add(movie)
    db_session.commit()

    # Update FTS5 index for tests
    db_session.execute(text("INSERT INTO movie_search(rowid, title) SELECT id, title FROM movies"))
    db_session.commit()

    for movie in movies:
        db_session.refresh(movie)

    return movies


@pytest.fixture
def movies_with_genres(db_session: Session, sample_movies: list[Movie]) -> list[Movie]:
    """Add genres to sample movies."""
    # First create unique genres
    genre_names = {"剧情", "犯罪", "喜剧", "动作", "悬疑"}
    genre_map = {}
    for name in genre_names:
        genre = Genre(name=name)
        db_session.add(genre)
    db_session.flush()

    genres_list = db_session.query(Genre).all()
    genre_map = {g.name: g.id for g in genres_list}

    genres_data = [
        (sample_movies[0].id, genre_map["剧情"]),
        (sample_movies[0].id, genre_map["犯罪"]),
        (sample_movies[1].id, genre_map["喜剧"]),
        (sample_movies[2].id, genre_map["动作"]),
        (sample_movies[2].id, genre_map["犯罪"]),
        (sample_movies[3].id, genre_map["剧情"]),
        (sample_movies[3].id, genre_map["悬疑"]),
        (sample_movies[4].id, genre_map["喜剧"]),
    ]
    for movie_id, genre_id in genres_data:
        db_session.add(MovieGenre(movie_id=movie_id, genre_id=genre_id))
    db_session.commit()
    return sample_movies

"""Service layer tests."""

import time

import pytest
from sqlalchemy import text

from app.database import Movie, MovieGenre
from app.services.import_service import ImportService


# @pytest.mark.skip(
#     reason="Import tests require complex database isolation setup with background threads"
# )
class TestImportService:
    """Tests for ImportService."""

    def test_singleton_pattern(self):
        """Test that ImportService is a singleton."""
        ImportService._instance = None
        service1 = ImportService()
        service2 = ImportService()
        assert service1 is service2

    def test_initial_status(self, client):
        """Test that initial status is idle."""
        ImportService._instance = None
        service = ImportService()
        assert service.status.status == "idle"

    def test_import_completes_successfully(
        self, client, populated_source_db, temp_source_db_path: str, db_session
    ):
        """Test that import process completes successfully."""
        ImportService._instance = None

        response = client.post("/api/import", json={"source_path": temp_source_db_path})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"

        for _ in range(50):
            time.sleep(0.2)
            status_response = client.get("/api/import/status")
            status = status_response.json()
            if status["status"] in ("completed", "failed"):
                break

        final_response = client.get("/api/import/status")
        final_status = final_response.json()
        assert final_status["status"] == "completed"
        assert final_status["processed"] == 6
        assert final_status["percentage"] == 100.0

        db_session.expire_all()
        result = db_session.execute(text("SELECT COUNT(*) FROM movies"))
        count = result.scalar()
        assert count == 6

        genre_result = db_session.execute(text("SELECT COUNT(*) FROM movie_genres"))
        genre_count = genre_result.scalar()
        assert genre_count == 10

    def test_import_clears_existing_data(
        self, client, sample_movies, populated_source_db, temp_source_db_path: str, db_session
    ):
        """Test that import clears existing data before importing new data."""
        ImportService._instance = None

        initial_count = db_session.query(Movie).count()
        assert initial_count == 6

        response = client.post("/api/import", json={"source_path": temp_source_db_path})
        assert response.status_code == 200

        for _ in range(50):
            time.sleep(0.2)
            status_response = client.get("/api/import/status")
            status = status_response.json()
            if status["status"] in ("completed", "failed"):
                break

        db_session.expire_all()
        final_count = db_session.query(Movie).count()
        assert final_count == 6

    def test_import_extracts_genres_correctly(
        self, client, populated_source_db, temp_source_db_path: str, db_session
    ):
        """Test that genres are extracted correctly from card_subtitle."""
        ImportService._instance = None
        client.post("/api/import", json={"source_path": temp_source_db_path})

        for _ in range(50):
            time.sleep(0.2)
            status_response = client.get("/api/import/status")
            status = status_response.json()
            if status["status"] == "completed":
                break

        db_session.expire_all()
        movie = db_session.query(Movie).filter(Movie.douban_id == "1001").first()
        assert movie is not None
        assert "剧情" in [g.genre for g in movie.genres]
        assert "犯罪" in [g.genre for g in movie.genres]

    def test_import_extracts_rating_count(
        self, client, populated_source_db, temp_source_db_path: str, db_session
    ):
        """Test that rating count is extracted from raw_data."""
        ImportService._instance = None
        client.post("/api/import", json={"source_path": temp_source_db_path})

        for _ in range(50):
            time.sleep(0.2)
            status_response = client.get("/api/import/status")
            status = status_response.json()
            if status["status"] == "completed":
                break

        db_session.expire_all()
        movie = db_session.query(Movie).filter(Movie.douban_id == "1001").first()
        assert movie is not None
        assert movie.rating_count == 1000

    def test_import_extracts_poster_url(
        self, client, populated_source_db, temp_source_db_path: str, db_session
    ):
        """Test that poster URL is extracted from raw_data."""
        ImportService._instance = None
        client.post("/api/import", json={"source_path": temp_source_db_path})

        for _ in range(50):
            time.sleep(0.2)
            status_response = client.get("/api/import/status")
            status = status_response.json()
            if status["status"] == "completed":
                break

        db_session.expire_all()
        movie1 = db_session.query(Movie).filter(Movie.douban_id == "1001").first()
        assert movie1 is not None
        assert movie1.poster_url == "http://example.com/p1.jpg"

        movie2 = db_session.query(Movie).filter(Movie.douban_id == "1002").first()
        assert movie2 is not None
        assert movie2.poster_url == "http://example.com/p2.jpg"

    def test_import_handles_null_rating(
        self, client, populated_source_db, temp_source_db_path: str, db_session
    ):
        """Test that null ratings are handled correctly."""
        ImportService._instance = None
        client.post("/api/import", json={"source_path": temp_source_db_path})

        for _ in range(50):
            time.sleep(0.2)
            status_response = client.get("/api/import/status")
            status = status_response.json()
            if status["status"] == "completed":
                break

        db_session.expire_all()
        movie = db_session.query(Movie).filter(Movie.douban_id == "1004").first()
        assert movie is not None
        assert movie.rating is None

    def test_import_handles_empty_raw_data(
        self, client, populated_source_db, temp_source_db_path: str, db_session
    ):
        """Test that empty raw_data is handled correctly."""
        ImportService._instance = None
        client.post("/api/import", json={"source_path": temp_source_db_path})

        for _ in range(50):
            time.sleep(0.2)
            status_response = client.get("/api/import/status")
            status = status_response.json()
            if status["status"] == "completed":
                break

        db_session.expire_all()
        movie = db_session.query(Movie).filter(Movie.douban_id == "1005").first()
        assert movie is not None
        assert movie.rating_count == 0
        assert movie.poster_url is None
        assert len(movie.genres) == 0

    def test_import_extracts_poster_url_from_cover_url_fallback(
        self, client, populated_source_db, temp_source_db_path: str, db_session
    ):
        """Test that poster URL is extracted from cover_url if pic is missing."""
        ImportService._instance = None
        client.post("/api/import", json={"source_path": temp_source_db_path})

        for _ in range(50):
            time.sleep(0.2)
            status_response = client.get("/api/import/status")
            status = status_response.json()
            if status["status"] == "completed":
                break

        db_session.expire_all()
        movie = db_session.query(Movie).filter(Movie.douban_id == "1300613").first()
        assert movie is not None
        assert movie.poster_url == "https://example.com/cover.jpg"


class TestMovieService:
    """Tests for MovieService."""

    def test_get_movies_no_results_for_unmatched_genres(self, client, movies_with_genres: list):
        """Test that filtering by non-existent genre returns no results."""
        response = client.get("/api/movies?genres=武侠")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

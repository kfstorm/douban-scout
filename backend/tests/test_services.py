"""Service layer tests."""

import time
from unittest.mock import patch

from sqlalchemy import text

from app.database import Movie
from app.services.import_service import ImportService


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
        headers = {"X-API-Key": "test-api-key"}

        response = client.post(
            "/api/import", json={"source_path": temp_source_db_path}, headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"

        for _ in range(50):
            time.sleep(0.2)
            status_response = client.get("/api/import/status", headers=headers)
            status = status_response.json()
            if status["status"] in ("completed", "failed"):
                break

        final_response = client.get("/api/import/status", headers=headers)
        final_status = final_response.json()
        assert final_status["status"] == "completed"
        # 7 original + 6 new (added 走出非洲, 青木瓜之味, 功夫, 岁月的童话, 云上的日子, 秋海棠)
        assert final_status["processed"] == 13
        assert final_status["percentage"] == 100.0

        db_session.expire_all()
        result = db_session.execute(text("SELECT COUNT(*) FROM movies"))
        count = result.scalar()
        assert count == 13

        genre_result = db_session.execute(text("SELECT COUNT(*) FROM movie_genres"))
        genre_count = genre_result.scalar()
        # Original: 12. New ones:
        # 青木瓜之味: 剧情 爱情 音乐 (3)
        # 功夫: 喜剧 动作 犯罪 奇幻 (4)
        # 岁月的童话: 剧情 爱情 动画 (3)
        # 走出非洲: 冒险 传记 剧情 爱情 (4)
        # 云上的日子: 剧情 爱情 情色 (3)
        # 秋海棠: 爱情 剧情 (2)
        # Total: 12 + 19 = 31
        assert genre_count == 31

    def test_import_clears_existing_data(
        self, client, sample_movies, populated_source_db, temp_source_db_path: str, db_session
    ):
        """Test that import clears existing data before importing new data."""
        ImportService._instance = None
        headers = {"X-API-Key": "test-api-key"}

        initial_count = db_session.query(Movie).count()
        # 12 because sample_movies fixture is called, and it uses the database
        # that already had some items, but wait, sample_movies adds its own.
        # Let's check conftest.py again.
        assert initial_count == 7

        response = client.post(
            "/api/import", json={"source_path": temp_source_db_path}, headers=headers
        )
        assert response.status_code == 200

        for _ in range(50):
            time.sleep(0.2)
            status_response = client.get("/api/import/status", headers=headers)
            status = status_response.json()
            if status["status"] in ("completed", "failed"):
                break

        # Close session to force new connection that sees the swapped file
        db_session.close()
        final_count = db_session.query(Movie).count()
        assert final_count == 13

    def test_import_extracts_genres_correctly(
        self, client, populated_source_db, temp_source_db_path: str, db_session
    ):
        """Test that genres are extracted correctly from card_subtitle."""
        ImportService._instance = None
        headers = {"X-API-Key": "test-api-key"}
        client.post("/api/import", json={"source_path": temp_source_db_path}, headers=headers)

        for _ in range(50):
            time.sleep(0.2)
            status_response = client.get("/api/import/status", headers=headers)
            status = status_response.json()
            if status["status"] == "completed":
                break

        db_session.expire_all()
        movie = db_session.query(Movie).filter(Movie.id == 1001).first()
        assert movie is not None
        genres = [g.genre_obj.name for g in movie.genres]
        assert "剧情" in genres
        assert "犯罪" in genres

    def test_import_extracts_genres_from_subtitle(
        self, client, populated_source_db, temp_source_db_path: str, db_session
    ):
        """Test that genres are extracted correctly from subtitle fallback."""
        ImportService._instance = None
        headers = {"X-API-Key": "test-api-key"}
        client.post("/api/import", json={"source_path": temp_source_db_path}, headers=headers)

        for _ in range(50):
            time.sleep(0.2)
            status_response = client.get("/api/import/status", headers=headers)
            status = status_response.json()
            if status["status"] == "completed":
                break

        db_session.expire_all()
        movie = db_session.query(Movie).filter(Movie.id == 1449961).first()
        assert movie is not None
        genres = [g.genre_obj.name for g in movie.genres]
        assert "纪录片" in genres
        assert "音乐" in genres

    def test_import_extracts_rating_count(
        self, client, populated_source_db, temp_source_db_path: str, db_session
    ):
        """Test that rating count is extracted from raw_data."""
        ImportService._instance = None
        headers = {"X-API-Key": "test-api-key"}
        client.post("/api/import", json={"source_path": temp_source_db_path}, headers=headers)

        for _ in range(50):
            time.sleep(0.2)
            status_response = client.get("/api/import/status", headers=headers)
            status = status_response.json()
            if status["status"] == "completed":
                break

        db_session.expire_all()
        movie = db_session.query(Movie).filter(Movie.id == 1001).first()
        assert movie is not None
        assert movie.rating_count == 1000

    def test_import_extracts_poster_url(
        self, client, populated_source_db, temp_source_db_path: str, db_session
    ):
        """Test that poster URL is extracted from raw_data."""
        ImportService._instance = None
        headers = {"X-API-Key": "test-api-key"}
        client.post("/api/import", json={"source_path": temp_source_db_path}, headers=headers)

        for _ in range(50):
            time.sleep(0.2)
            status_response = client.get("/api/import/status", headers=headers)
            status = status_response.json()
            if status["status"] == "completed":
                break

        db_session.expire_all()
        movie1 = db_session.query(Movie).filter(Movie.id == 1001).first()
        assert movie1 is not None
        assert "http://example.com/p1.jpg" in [p.url for p in movie1.posters]

        movie2 = db_session.query(Movie).filter(Movie.id == 1002).first()
        assert movie2 is not None
        assert "http://example.com/p2.jpg" in [p.url for p in movie2.posters]

    def test_import_handles_null_rating(
        self, client, populated_source_db, temp_source_db_path: str, db_session
    ):
        """Test that null ratings are handled correctly."""
        ImportService._instance = None
        headers = {"X-API-Key": "test-api-key"}
        client.post("/api/import", json={"source_path": temp_source_db_path}, headers=headers)

        for _ in range(50):
            time.sleep(0.2)
            status_response = client.get("/api/import/status", headers=headers)
            status = status_response.json()
            if status["status"] == "completed":
                break

        db_session.expire_all()
        movie = db_session.query(Movie).filter(Movie.id == 1004).first()
        assert movie is not None
        assert movie.rating is None

    def test_import_handles_empty_raw_data(
        self, client, populated_source_db, temp_source_db_path: str, db_session
    ):
        """Test that empty raw_data is handled correctly."""
        ImportService._instance = None
        headers = {"X-API-Key": "test-api-key"}
        client.post("/api/import", json={"source_path": temp_source_db_path}, headers=headers)

        for _ in range(50):
            time.sleep(0.2)
            status_response = client.get("/api/import/status", headers=headers)
            status = status_response.json()
            if status["status"] == "completed":
                break

        db_session.expire_all()
        movie = db_session.query(Movie).filter(Movie.id == 1005).first()
        assert movie is not None
        assert movie.rating_count == 0
        assert len(movie.posters) == 0
        assert len(movie.genres) == 0

    def test_import_extracts_poster_url_from_cover_url_fallback(
        self, client, populated_source_db, temp_source_db_path: str, db_session
    ):
        """Test that poster URL is extracted from cover_url if pic is missing."""
        ImportService._instance = None
        headers = {"X-API-Key": "test-api-key"}
        client.post("/api/import", json={"source_path": temp_source_db_path}, headers=headers)

        for _ in range(50):
            time.sleep(0.2)
            status_response = client.get("/api/import/status", headers=headers)
            status = status_response.json()
            if status["status"] == "completed":
                break

        db_session.expire_all()
        movie = db_session.query(Movie).filter(Movie.id == 1300613).first()
        assert movie is not None
        assert "https://example.com/cover.jpg" in [p.url for p in movie.posters]

    def test_import_rollback_on_failure(
        self, client, sample_movies, populated_source_db, temp_source_db_path: str, db_session
    ):
        """Test that if an import fails, the database is rolled back to its previous state."""
        ImportService._instance = None
        headers = {"X-API-Key": "test-api-key"}

        # Initial count should be from sample_movies
        initial_count = db_session.query(Movie).count()
        assert initial_count == 7

        def side_effect_fail(*args, **kwargs):
            raise Exception("Simulated import failure")

        with patch.object(ImportService, "_insert_batch", side_effect=side_effect_fail):
            response = client.post(
                "/api/import", json={"source_path": temp_source_db_path}, headers=headers
            )
            assert response.status_code == 200

            # Wait for import to fail
            status = {}
            for _ in range(50):
                time.sleep(0.1)
                status = client.get("/api/import/status", headers=headers).json()
                if status["status"] == "failed":
                    break

            assert status["status"] == "failed"
            assert "Simulated import failure" in status["message"]

        # Check database state - it should STILL have 7 movies if atomic
        db_session.expire_all()
        final_count = db_session.query(Movie).count()
        assert final_count == 7

    def test_import_robustness(
        self, client, populated_source_db, temp_source_db_path: str, db_session
    ):
        """Test that different detail_source formats are handled correctly."""
        ImportService._instance = None
        headers = {"X-API-Key": "test-api-key"}
        client.post("/api/import", json={"source_path": temp_source_db_path}, headers=headers)

        for _ in range(50):
            time.sleep(0.2)
            status_response = client.get("/api/import/status", headers=headers)
            status = status_response.json()
            if status["status"] == "completed":
                break

        db_session.expire_all()

        # 1. Test top_list format (走出非洲)
        movie_out_of_africa = db_session.query(Movie).filter(Movie.id == 1291840).first()
        assert movie_out_of_africa is not None
        assert movie_out_of_africa.rating_count == 102121
        genres = [g.genre_obj.name for g in movie_out_of_africa.genres]
        assert set(genres) == {"冒险", "传记", "剧情", "爱情"}
        regions = [r.region_obj.name for r in movie_out_of_africa.regions]
        assert "美国" in regions

        # 2. Test rexxar API format (岁月的童话)
        movie_yesterday = db_session.query(Movie).filter(Movie.id == 1291588).first()
        assert movie_yesterday is not None
        assert movie_yesterday.rating_count == 152316
        genres = [g.genre_obj.name for g in movie_yesterday.genres]
        assert set(genres) == {"剧情", "爱情", "动画"}
        regions = [r.region_obj.name for r in movie_yesterday.regions]
        assert "日本" in regions

        # 3. Test doulist/subtitle format (青木瓜之味)
        movie_papaya = db_session.query(Movie).filter(Movie.id == 1291553).first()
        assert movie_papaya is not None
        genres = [g.genre_obj.name for g in movie_papaya.genres]
        assert "越南" not in genres  # 越南 is a region
        assert set(genres) == {"剧情", "爱情", "音乐"}
        regions = [r.region_obj.name for r in movie_papaya.regions]
        assert "越南" in regions
        assert "法国" in regions

    def test_import_extracts_from_tags_fallback(
        self, client, populated_source_db, temp_source_db_path: str, db_session
    ):
        """Test that genres and regions are extracted from tags when other fields are missing."""
        ImportService._instance = None
        headers = {"X-API-Key": "test-api-key"}
        client.post("/api/import", json={"source_path": temp_source_db_path}, headers=headers)

        for _ in range(50):
            time.sleep(0.2)
            status_response = client.get("/api/import/status", headers=headers)
            status = status_response.json()
            if status["status"] == "completed":
                break

        db_session.expire_all()
        # ID 1298274 (秋海棠) has '大陆', '台湾', '爱情', '剧情' in tags
        movie = db_session.query(Movie).filter(Movie.id == 1298274).first()
        assert movie is not None
        genres = [g.genre_obj.name for g in movie.genres]
        assert "爱情" in genres
        assert "剧情" in genres
        regions = [r.region_obj.name for r in movie.regions]
        assert "大陆" in regions
        assert "台湾" in regions

    def test_import_does_not_extract_from_photos_field(
        self, client, populated_source_db, temp_source_db_path: str, db_session
    ):
        """Test that images from the 'photos' field are NOT extracted as posters."""
        ImportService._instance = None
        headers = {"X-API-Key": "test-api-key"}
        client.post("/api/import", json={"source_path": temp_source_db_path}, headers=headers)

        for _ in range(50):
            time.sleep(0.2)
            status_response = client.get("/api/import/status", headers=headers)
            status = status_response.json()
            if status["status"] == "completed":
                break

        db_session.expire_all()
        movie = db_session.query(Movie).filter(Movie.id == 1449961).first()
        assert movie is not None
        # Should have 0 posters because 'pic' and 'cover_url' are missing,
        # and 'photos' should be ignored.
        assert len(movie.posters) == 0
        poster_urls = [p.url for p in movie.posters]
        assert "https://example.com/photo1.jpg" not in poster_urls
        assert "https://example.com/photo2.jpg" not in poster_urls


class TestMovieService:
    """Tests for MovieService."""

    def test_get_movies_no_results_for_unmatched_genres(self, client, movies_with_genres: list):
        """Test that filtering by non-existent genre returns no results."""
        response = client.get("/api/movies?genres=武侠")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

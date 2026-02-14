"""Tests for region extraction and filtering."""

import time

from app.database import Movie
from app.services.import_service import ImportService


class TestRegionImport:
    """Tests for region extraction during import."""

    def test_import_extracts_regions_correctly(
        self, client, populated_source_db, temp_source_db_path: str, db_session
    ):
        """Test that regions are extracted correctly from raw_data."""
        ImportService._instance = None
        headers = {"X-API-Key": "test-api-key"}
        client.post("/api/import", json={"source_path": temp_source_db_path}, headers=headers)

        for _ in range(50):
            time.sleep(0.1)
            status_response = client.get("/api/import/status", headers=headers)
            status = status_response.json()
            if status["status"] == "completed":
                break

        db_session.expire_all()
        # Test movie 1001: has both countries list and card_subtitle
        movie1 = db_session.query(Movie).filter(Movie.id == 1001).first()
        assert movie1 is not None
        regions1 = [r.region_obj.name for r in movie1.regions]
        assert "美国" in regions1
        assert "中国大陆" in regions1

        # Test movie 1002: has Hong Kong in card_subtitle, no countries list
        movie2 = db_session.query(Movie).filter(Movie.id == 1002).first()
        assert movie2 is not None
        regions2 = [r.region_obj.name for r in movie2.regions]
        assert "香港" in regions2


class TestRegionAPI:
    """Tests for region-related API endpoints."""

    def test_get_regions_empty(self, client):
        """Test getting regions from empty database."""
        response = client.get("/api/movies/regions")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_regions_with_data(self, client, movies_with_regions: list):
        """Test getting regions with sample data."""
        response = client.get("/api/movies/regions")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

        region_names = [r["region"] for r in data]
        assert "美国" in region_names
        assert "香港" in region_names

    def test_get_movies_filter_by_region(self, client, movies_with_regions: list):
        """Test filtering movies by region."""
        # movies_with_regions[0] and movies_with_regions[3] have "美国"
        response = client.get("/api/movies?regions=美国")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        for movie in data["items"]:
            assert "美国" in movie["regions"]

    def test_get_movies_filter_by_multiple_regions(self, client, movies_with_regions: list):
        """Test filtering movies by multiple regions (OR logic)."""
        # "日本" has 1 movie, "香港" has 2 movies
        response = client.get("/api/movies?regions=日本,香港")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        for movie in data["items"]:
            assert "日本" in movie["regions"] or "香港" in movie["regions"]

    def test_get_stats_includes_regions(self, client, movies_with_regions: list):
        """Test that stats include total_regions."""
        response = client.get("/api/movies/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_regions" in data
        assert data["total_regions"] == 4

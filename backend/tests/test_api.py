"""API endpoint tests."""

import os
import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client: TestClient):
        """Test health check returns healthy status."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data == {"status": "healthy"}


class TestMoviesEndpoint:
    """Tests for movies list endpoint."""

    def test_get_movies_empty(self, client: TestClient):
        """Test getting movies from empty database."""
        response = client.get("/api/movies")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["next_cursor"] is None
        assert data["total"] == 0

    def test_get_movies_with_data(self, client: TestClient, sample_movies: list):
        """Test getting movies with sample data."""
        response = client.get("/api/movies")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["total"] == 5

    def test_get_movies_limit(self, client: TestClient, sample_movies: list):
        """Test movies limit parameter."""
        response = client.get("/api/movies?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["next_cursor"] is not None
        assert data["total"] == 5

    def test_get_movies_limit_max_validation(self, client: TestClient):
        """Test limit cannot exceed 100."""
        response = client.get("/api/movies?limit=200")
        assert response.status_code == 422

    def test_get_movies_limit_min_validation(self, client: TestClient):
        """Test limit cannot be less than 1."""
        response = client.get("/api/movies?limit=0")
        assert response.status_code == 422

    def test_get_movies_filter_by_type(self, client: TestClient, sample_movies: list):
        """Test filtering movies by type."""
        response = client.get("/api/movies?type=movie")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert all(m["type"] == "movie" for m in data["items"])

    def test_get_movies_filter_by_tv(self, client: TestClient, sample_movies: list):
        """Test filtering movies by type=tv."""
        response = client.get("/api/movies?type=tv")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert all(m["type"] == "tv" for m in data["items"])

    def test_get_movies_filter_by_min_rating(self, client: TestClient, sample_movies: list):
        """Test filtering movies by minimum rating."""
        response = client.get("/api/movies?min_rating=8.0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert all(m["rating"] >= 8.0 for m in data["items"])

    def test_get_movies_filter_by_max_rating(self, client: TestClient, sample_movies: list):
        """Test filtering movies by maximum rating."""
        response = client.get("/api/movies?max_rating=7.5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert all(m["rating"] <= 7.5 for m in data["items"])

    def test_get_movies_filter_by_rating_range(self, client: TestClient, sample_movies: list):
        """Test filtering movies by rating range."""
        response = client.get("/api/movies?min_rating=7.0&max_rating=8.5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 4
        for m in data["items"]:
            assert 7.0 <= m["rating"] <= 8.5

    def test_get_movies_filter_by_genres(self, client: TestClient, movies_with_genres: list):
        """Test filtering movies by genres (AND logic)."""
        response = client.get("/api/movies?genres=剧情")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2

    def test_get_movies_filter_by_multiple_genres(
        self, client: TestClient, movies_with_genres: list
    ):
        """Test filtering movies by multiple genres."""
        response = client.get("/api/movies?genres=剧情,犯罪")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "剧情" in data["items"][0]["genres"]
        assert "犯罪" in data["items"][0]["genres"]

    def test_get_movies_filter_by_invalid_genre(self, client: TestClient, movies_with_genres: list):
        """Test filtering with invalid genre ignores it gracefully."""
        response = client.get("/api/movies?genres=剧情,invalid_genre")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2

    def test_get_movies_search(self, client: TestClient, sample_movies: list):
        """Test searching movies by title."""
        response = client.get("/api/movies?search=Drama")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Drama Movie"

    def test_get_movies_search_no_results(self, client: TestClient, sample_movies: list):
        """Test search with no results."""
        response = client.get("/api/movies?search=nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_get_movies_sort_by_rating(self, client: TestClient, sample_movies: list):
        """Test sorting movies by rating."""
        response = client.get("/api/movies?sort_by=rating&sort_order=desc")
        assert response.status_code == 200
        data = response.json()
        ratings = [m["rating"] for m in data["items"]]
        assert ratings == sorted(ratings, reverse=True)

    def test_get_movies_sort_by_rating_count(self, client: TestClient, sample_movies: list):
        """Test sorting movies by rating count."""
        response = client.get("/api/movies?sort_by=rating_count&sort_order=desc")
        assert response.status_code == 200
        data = response.json()
        counts = [m["rating_count"] for m in data["items"]]
        assert counts == sorted(counts, reverse=True)

    def test_get_movies_sort_ascending(self, client: TestClient, sample_movies: list):
        """Test sorting movies in ascending order."""
        response = client.get("/api/movies?sort_by=rating&sort_order=asc")
        assert response.status_code == 200
        data = response.json()
        ratings = [m["rating"] for m in data["items"]]
        assert ratings == sorted(ratings)

    def test_get_movies_cursor_pagination(self, client: TestClient, sample_movies: list):
        """Test cursor-based pagination."""
        response1 = client.get("/api/movies?limit=2&sort_by=rating&sort_order=desc")
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["items"]) == 2
        assert data1["next_cursor"] is not None

        cursor = data1["next_cursor"]
        response2 = client.get(
            f"/api/movies?limit=2&sort_by=rating&sort_order=desc&cursor={cursor}"
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["items"]) <= 2

        if data2["next_cursor"] is not None:
            response3 = client.get(
                f"/api/movies?limit=2&sort_by=rating&sort_order=desc&cursor={data2['next_cursor']}"
            )
            data3 = response3.json()
            assert len(data3["items"]) <= 2

    def test_get_movies_invalid_cursor(self, client: TestClient, sample_movies: list):
        """Test invalid cursor is handled gracefully."""
        response = client.get("/api/movies?cursor=invalid_cursor")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5

    def test_get_movies_combined_filters(self, client: TestClient, movies_with_genres: list):
        """Test combining multiple filters."""
        response = client.get("/api/movies?type=movie&min_rating=7.0&genres=犯罪")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        for m in data["items"]:
            assert m["type"] == "movie"
            assert m["rating"] >= 7.0
            assert "犯罪" in m["genres"]


class TestGenresEndpoint:
    """Tests for genres endpoint."""

    def test_get_genres_empty(self, client: TestClient):
        """Test getting genres from empty database."""
        response = client.get("/api/movies/genres")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_genres_with_data(self, client: TestClient, movies_with_genres: list):
        """Test getting genres with sample data."""
        response = client.get("/api/movies/genres")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

    def test_get_genres_filter_by_type(self, client: TestClient, movies_with_genres: list):
        """Test filtering genres by type."""
        response = client.get("/api/movies/genres?type=movie")
        assert response.status_code == 200
        data = response.json()
        for genre in data:
            assert genre["count"] == sum(
                1
                for m in movies_with_genres
                if m.type == "movie" and genre["genre"] in [g.genre for g in m.genres]
            )

    def test_get_genres_filter_by_tv(self, client: TestClient, movies_with_genres: list):
        """Test filtering genres by type=tv."""
        response = client.get("/api/movies/genres?type=tv")
        assert response.status_code == 200
        data = response.json()
        for genre in data:
            assert genre["count"] == sum(
                1
                for m in movies_with_genres
                if m.type == "tv" and genre["genre"] in [g.genre for g in m.genres]
            )


class TestStatsEndpoint:
    """Tests for stats endpoint."""

    def test_get_stats_empty(self, client: TestClient):
        """Test getting stats from empty database."""
        response = client.get("/api/movies/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_movies"] == 0
        assert data["total_tv"] == 0
        assert data["avg_rating"] == 0.0
        assert data["total_genres"] == 0

    def test_get_stats_with_data(self, client: TestClient, sample_movies: list):
        """Test getting stats with sample data."""
        response = client.get("/api/movies/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_movies"] == 3
        assert data["total_tv"] == 2
        assert data["total_genres"] == 0


class TestImportEndpoint:
    """Tests for data import endpoint."""

    def test_get_import_status_idle(self, client: TestClient):
        """Test getting import status when idle."""
        response = client.get("/api/import/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "idle"

    def test_start_import_file_not_found(self, client: TestClient):
        """Test importing from non-existent file returns 404."""
        response = client.post("/api/import", json={"source_path": "/nonexistent/file.sqlite3"})
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_start_import_already_running(
        self, client: TestClient, populated_source_db, temp_source_db_path: str
    ):
        """Test that starting import while already running returns current status."""
        response1 = client.post("/api/import", json={"source_path": temp_source_db_path})
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["status"] == "running"

        response2 = client.post("/api/import", json={"source_path": temp_source_db_path})
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["status"] == "running"
        assert data2["processed"] == data1["processed"]

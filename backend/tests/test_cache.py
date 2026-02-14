"""Tests for caching mechanism."""

import time
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.cache import cache_manager, cached
from app.services.movie_service import movie_service


class TestCache:
    """Test suite for CacheManager and cached decorator."""

    def setup_method(self) -> None:
        """Clear cache before each test."""
        cache_manager.clear()

    def test_cache_set_get(self) -> None:
        """Test basic set and get operations."""
        cache_manager.set("test_key", "test_value")
        assert cache_manager.get("test_key") == "test_value"
        assert cache_manager.get("non_existent") is None

    def test_cache_clear(self) -> None:
        """Test cache clearing."""
        cache_manager.set("k1", "v1")
        cache_manager.set("k2", "v2")
        cache_manager.clear()
        assert cache_manager.get("k1") is None
        assert cache_manager.get("k2") is None

    def test_cached_decorator(self) -> None:
        """Test that the cached decorator actually caches results."""
        call_count = 0

        @cached(prefix="test")
        def expensive_func(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call - miss
        assert expensive_func(10) == 20
        assert call_count == 1

        # Second call - hit
        assert expensive_func(10) == 20
        assert call_count == 1

        # Different arg - miss
        assert expensive_func(20) == 40
        assert call_count == 2

    def test_cached_decorator_skips_session(self) -> None:
        """Test that Session objects are excluded from cache keys."""
        call_count = 0
        mock_session1 = MagicMock(spec=Session)
        mock_session2 = MagicMock(spec=Session)

        @cached(prefix="session_test")
        def func_with_session(db: Session, x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x

        # Call with session 1
        assert func_with_session(mock_session1, 5) == 5
        assert call_count == 1

        # Call with session 2 - should be a cache hit because sessions are ignored
        assert func_with_session(mock_session2, 5) == 5
        assert call_count == 1


class TestMovieServiceCaching:
    """Integration tests for MovieService caching."""

    def test_get_genres_caching(self, db_session: Session) -> None:
        """Test that get_genres is cached."""
        # Use a real or mock session, the result should be cached
        with patch.object(Session, "query", wraps=db_session.query) as mock_query:
            # Clear cache to ensure a fresh start
            cache_manager.clear()

            # First call
            movie_service.get_genres(db_session)
            initial_call_count = mock_query.call_count
            assert initial_call_count > 0

            # Second call - should be a hit, no new queries
            movie_service.get_genres(db_session)
            assert mock_query.call_count == initial_call_count

    def test_get_stats_caching(self, db_session: Session) -> None:
        """Test that get_stats is cached."""
        with patch.object(Session, "query", wraps=db_session.query) as mock_query:
            cache_manager.clear()

            movie_service.get_stats(db_session)
            initial_call_count = mock_query.call_count

            movie_service.get_stats(db_session)
            assert mock_query.call_count == initial_call_count

    def test_movie_count_caching(self, db_session: Session) -> None:
        """Test that the filtered count in get_movies is cached."""
        cache_manager.clear()

        # We need to track calls to the count part.
        # Since _get_filtered_count is decorated, it should only execute once for same filters.
        with patch.object(
            movie_service, "_apply_filters", wraps=movie_service._apply_filters
        ) as mock_apply:
            # First call to get_movies
            movie_service.get_movies(db_session, limit=1)
            # _apply_filters is called twice: once for count, once for items
            assert mock_apply.call_count == 2

            # Second call to get_movies with same filters
            movie_service.get_movies(db_session, limit=1)
            # Only 1 more call to _apply_filters (for items), because count is cached
            assert mock_apply.call_count == 3

    def test_cache_invalidation_on_import(
        self, client, populated_source_db, temp_source_db_path, db_session
    ):
        """Test that import clears the cache."""
        cache_manager.clear()
        headers = {"X-API-Key": "test-api-key"}

        # Populate cache
        movie_service.get_stats(db_session)
        assert cache_manager.get("stats") is not None

        # Trigger import
        response = client.post(
            "/api/import", json={"source_path": temp_source_db_path}, headers=headers
        )
        assert response.status_code == 200

        # Wait for completion
        for _ in range(50):
            time.sleep(0.1)
            status = client.get("/api/import/status", headers=headers).json()
            if status["status"] == "completed":
                break

        # Cache should be empty now
        assert cache_manager.get("stats") is None

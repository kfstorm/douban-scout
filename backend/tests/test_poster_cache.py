"""Tests for poster caching functionality."""

import os
import time
from unittest.mock import patch

import pytest

from app.services.poster_service import PosterCacheService


class TestPosterCacheService:
    """Tests for PosterCacheService."""

    @pytest.fixture
    def temp_cache_service(self, tmp_path):
        """Create a temporary cache service for testing."""
        with patch("app.services.poster_service.settings") as mock_settings:
            mock_settings.data_dir = str(tmp_path)
            mock_settings.poster_cache_ttl = 365
            service = PosterCacheService()
            yield service

    def test_cache_dir_creation(self, tmp_path):
        """Test that cache directory is created automatically."""
        with patch("app.services.poster_service.settings") as mock_settings:
            mock_settings.data_dir = str(tmp_path)
            mock_settings.poster_cache_ttl = 365
            service = PosterCacheService()
            assert service.cache_dir.exists()
            assert service.cache_dir == tmp_path / "cache/posters"

    def test_save_poster(self, temp_cache_service):
        """Test saving a poster to cache."""
        movie_id = 12345
        content = b"fake image content"
        content_type = "image/jpeg"

        cache_path = temp_cache_service.save_poster(movie_id, content, content_type)

        assert cache_path is not None
        assert cache_path.exists()
        assert cache_path.read_bytes() == content
        assert cache_path.suffix == ".jpg"
        assert cache_path.name == "12345.jpg"

    def test_save_poster_webp(self, temp_cache_service):
        """Test saving a webp poster."""
        movie_id = 12346
        content = b"fake webp content"
        content_type = "image/webp"

        cache_path = temp_cache_service.save_poster(movie_id, content, content_type)

        assert cache_path is not None
        assert cache_path.suffix == ".webp"
        assert cache_path.name == "12346.webp"

    def test_get_cached_poster_hit(self, temp_cache_service):
        """Test retrieving a cached poster when it exists."""
        movie_id = 12345
        content = b"fake image content"
        content_type = "image/jpeg"

        # Save first
        temp_cache_service.save_poster(movie_id, content, content_type)

        # Retrieve
        result = temp_cache_service.get_cached_poster(movie_id)

        assert result is not None
        cache_path, returned_content_type = result
        assert cache_path.exists()
        assert cache_path.read_bytes() == content
        assert returned_content_type == "image/jpeg"

    def test_get_cached_poster_miss(self, temp_cache_service):
        """Test retrieving a poster when cache doesn't exist."""
        movie_id = 99999

        result = temp_cache_service.get_cached_poster(movie_id)

        assert result is None

    def test_get_cached_poster_expired(self, temp_cache_service):
        """Test that expired cache is not returned."""
        movie_id = 12345
        content = b"fake image content"
        content_type = "image/jpeg"

        # Save with short TTL
        temp_cache_service.ttl_days = 1
        temp_cache_service.save_poster(movie_id, content, content_type)

        # Verify it's there
        assert temp_cache_service.get_cached_poster(movie_id) is not None

        # Simulate expiration by modifying mtime
        cache_path = temp_cache_service.cache_dir / "12345.jpg"
        old_time = time.time() - (2 * 24 * 3600)  # 2 days ago
        cache_path.touch()
        os.utime(cache_path, (old_time, old_time))

        # Should return None for expired cache
        result = temp_cache_service.get_cached_poster(movie_id)
        assert result is None

    def test_save_poster_replaces_existing(self, temp_cache_service):
        """Test that saving a poster replaces any existing cached file."""
        movie_id = 12345

        # Save first version
        temp_cache_service.save_poster(movie_id, b"old content", "image/jpeg")

        # Save new version with different format
        temp_cache_service.save_poster(movie_id, b"new content", "image/webp")

        # Should only have webp file now
        cache_files = list(temp_cache_service.cache_dir.glob(f"{movie_id}.*"))
        assert len(cache_files) == 1
        assert cache_files[0].suffix == ".webp"
        assert cache_files[0].read_bytes() == b"new content"

    def test_is_cache_valid_empty_file(self, temp_cache_service):
        """Test that empty cache files are considered invalid."""
        movie_id = 12345

        # Create empty file
        cache_path = temp_cache_service.cache_dir / f"{movie_id}.jpg"
        cache_path.write_bytes(b"")

        assert not temp_cache_service.is_cache_valid(cache_path)

    def test_content_type_guessing(self, temp_cache_service):
        """Test content type guessing from file extensions."""
        test_cases = [
            (".jpg", "image/jpeg"),
            (".jpeg", "image/jpeg"),
            (".png", "image/png"),
            (".webp", "image/webp"),
            (".gif", "image/gif"),
            (".avif", "image/avif"),
            (".svg", "image/svg+xml"),
            (".unknown", "image/jpeg"),  # Default
        ]

        for ext, expected_type in test_cases:
            result = temp_cache_service._guess_content_type_from_extension(ext)
            assert result == expected_type

    def test_extension_from_content_type(self, temp_cache_service):
        """Test extension mapping from content type."""
        test_cases = [
            ("image/jpeg", ".jpg"),
            ("image/jpg", ".jpg"),
            ("image/png", ".png"),
            ("image/webp", ".webp"),
            ("image/gif", ".gif"),
            ("image/avif", ".avif"),
            ("image/svg+xml", ".svg"),
            ("image/unknown", ".jpg"),  # Default
            ("image/jpeg; charset=utf-8", ".jpg"),  # With charset
        ]

        for content_type, expected_ext in test_cases:
            result = temp_cache_service._get_extension_from_content_type(content_type)
            assert result == expected_ext

    def test_clear_cache(self, temp_cache_service):
        """Test clearing all cached posters."""
        # Add some cache files
        temp_cache_service.save_poster(1, b"content1", "image/jpeg")
        temp_cache_service.save_poster(2, b"content2", "image/png")
        temp_cache_service.save_poster(3, b"content3", "image/webp")

        # Clear cache
        count = temp_cache_service.clear_cache()

        assert count == 3
        assert len(list(temp_cache_service.cache_dir.glob("*"))) == 0

    def test_cache_default_ttl(self, tmp_path):
        """Test that cache service uses settings for default TTL."""
        with patch("app.services.poster_service.settings") as mock_settings:
            mock_settings.data_dir = str(tmp_path)
            mock_settings.poster_cache_ttl = 100
            service = PosterCacheService()
            assert service.ttl_days == 100

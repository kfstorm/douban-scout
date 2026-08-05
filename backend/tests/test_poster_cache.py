"""Tests for poster caching functionality."""

import asyncio
import io
import os
import time
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from PIL import Image
from PIL.features import check as pillow_features

from app.main import _poster_cache_cleanup_loop, lifespan
from app.services.poster_service import PosterCacheService


def _make_image(width: int, height: int) -> bytes:
    """Create a small PNG image to use as poster content."""
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (180, 120, 90)).save(buffer, format="PNG")
    return buffer.getvalue()


class TestPosterCacheService:
    """Tests for PosterCacheService."""

    @pytest.fixture
    def temp_cache_service(self, tmp_path):
        """Create a temporary cache service for testing."""
        with patch("app.services.poster_service.settings") as mock_settings:
            mock_settings.data_dir = str(tmp_path)
            mock_settings.poster_cache_ttl = 365
            mock_settings.poster_encode_format = "original"
            mock_settings.poster_encode_quality = 80
            mock_settings.poster_max_width = 0
            service = PosterCacheService()
            yield service

    def test_cache_dir_creation(self, tmp_path):
        """Test that cache directory is created automatically."""
        with patch("app.services.poster_service.settings") as mock_settings:
            mock_settings.data_dir = str(tmp_path)
            mock_settings.poster_cache_ttl = 365
            mock_settings.poster_encode_format = "original"
            mock_settings.poster_encode_quality = 80
            mock_settings.poster_max_width = 0
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

    def test_clear_expired_cache_removes_expired_files(
        self, temp_cache_service: PosterCacheService
    ) -> None:
        """Test that expired cache files are removed."""
        temp_cache_service.ttl_days = 1
        expired_path = temp_cache_service.save_poster(12345, b"expired", "image/jpeg")
        current_path = temp_cache_service.save_poster(12346, b"current", "image/jpeg")

        assert expired_path is not None
        assert current_path is not None
        old_time = time.time() - (2 * 24 * 3600)
        os.utime(expired_path, (old_time, old_time))
        unrelated_path = temp_cache_service.cache_dir / "metadata.json"
        unrelated_path.write_bytes(b"metadata")
        os.utime(unrelated_path, (old_time, old_time))

        removed_count = temp_cache_service.clear_expired_cache()

        assert removed_count == 1
        assert not expired_path.exists()
        assert current_path.exists()
        assert unrelated_path.exists()

    def test_clear_expired_cache_keeps_unexpired_files(
        self, temp_cache_service: PosterCacheService
    ) -> None:
        """Test that unexpired cache files are kept."""
        cache_path = temp_cache_service.save_poster(12345, b"current", "image/jpeg")

        assert cache_path is not None
        assert temp_cache_service.clear_expired_cache() == 0
        assert cache_path.exists()

    @pytest.mark.asyncio
    async def test_lifespan_cleans_expired_cache_on_startup(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that application startup triggers poster cache cleanup."""
        cleanup = patch("app.main.poster_cache_service.clear_expired_cache", return_value=0)
        monkeypatch.setattr("app.main.get_db_path", lambda: "/tmp/test.db")

        with cleanup as cleanup_mock:
            async with lifespan(FastAPI()):
                pass

        cleanup_mock.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_periodic_cleanup_runs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that the background task runs periodic poster cache cleanup."""
        cleanup = patch("app.main.poster_cache_service.clear_expired_cache", return_value=0)
        sleep_calls = 0

        async def sleep(_: float) -> None:
            nonlocal sleep_calls
            sleep_calls += 1
            if sleep_calls == 2:
                raise asyncio.CancelledError

        monkeypatch.setattr("app.main.asyncio.sleep", sleep)

        with cleanup as cleanup_mock, pytest.raises(asyncio.CancelledError):
            await _poster_cache_cleanup_loop()

        assert cleanup_mock.call_count == 1

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

    def test_save_poster_encodes_to_webp(self, temp_cache_service):
        """Test that saving a poster re-encodes it to the configured webp format."""
        with patch("app.services.poster_service.settings") as mock_settings:
            mock_settings.poster_encode_format = "webp"
            mock_settings.poster_encode_quality = 75
            mock_settings.poster_max_width = 0
            cache_path = temp_cache_service.save_poster(20001, _make_image(540, 800), "image/png")

        assert cache_path is not None
        assert cache_path.suffix == ".webp"
        with Image.open(cache_path) as image:
            assert image.format == "WEBP"
            assert image.size == (540, 800)

    @pytest.mark.skipif(not pillow_features("avif"), reason="Pillow built without AVIF support")
    def test_save_poster_encodes_to_avif(self, temp_cache_service):
        """Test that saving a poster re-encodes it to the configured avif format."""
        with patch("app.services.poster_service.settings") as mock_settings:
            mock_settings.poster_encode_format = "avif"
            mock_settings.poster_encode_quality = 50
            mock_settings.poster_max_width = 0
            cache_path = temp_cache_service.save_poster(20002, _make_image(540, 800), "image/jpeg")

        assert cache_path is not None
        assert cache_path.suffix == ".avif"
        with Image.open(cache_path) as image:
            assert image.format == "AVIF"

    def test_save_poster_encodes_to_jpeg(self, temp_cache_service):
        """Test that saving a poster re-encodes it to jpeg and drops alpha."""
        with patch("app.services.poster_service.settings") as mock_settings:
            mock_settings.poster_encode_format = "jpeg"
            mock_settings.poster_encode_quality = 80
            mock_settings.poster_max_width = 0
            cache_path = temp_cache_service.save_poster(20005, _make_image(540, 800), "image/png")

        assert cache_path is not None
        assert cache_path.suffix == ".jpg"
        with Image.open(cache_path) as image:
            assert image.format == "JPEG"
            assert image.mode in ("RGB", "L")

    def test_save_poster_resizes_to_max_width(self, temp_cache_service):
        """Test that saving a poster downscales to the configured max width."""
        with patch("app.services.poster_service.settings") as mock_settings:
            mock_settings.poster_encode_format = "webp"
            mock_settings.poster_encode_quality = 75
            mock_settings.poster_max_width = 400
            cache_path = temp_cache_service.save_poster(20003, _make_image(540, 810), "image/jpeg")

        assert cache_path is not None
        with Image.open(cache_path) as image:
            assert image.width == 400
            assert image.height == 600

    def test_save_poster_keeps_smaller_than_max_width(self, temp_cache_service):
        """Test that saving a small poster does not upscale it."""
        with patch("app.services.poster_service.settings") as mock_settings:
            mock_settings.poster_encode_format = "webp"
            mock_settings.poster_encode_quality = 75
            mock_settings.poster_max_width = 400
            cache_path = temp_cache_service.save_poster(20004, _make_image(200, 300), "image/jpeg")

        assert cache_path is not None
        with Image.open(cache_path) as image:
            assert image.size == (200, 300)

    def test_save_poster_original_format_keeps_bytes(self, temp_cache_service):
        """Test that the original format stores bytes without re-encoding."""
        content = _make_image(120, 180)
        cache_path = temp_cache_service.save_poster(20006, content, "image/png")

        assert cache_path is not None
        assert cache_path.suffix == ".png"
        assert cache_path.read_bytes() == content

    def test_get_cached_poster_lazy_reencode_on_format_change(self, temp_cache_service):
        """Test that a cache with an outdated format is re-encoded on read."""
        content = _make_image(540, 800)
        with patch("app.services.poster_service.settings") as mock_settings:
            mock_settings.poster_encode_format = "original"
            temp_cache_service.save_poster(20007, content, "image/png")

        with patch("app.services.poster_service.settings") as mock_settings:
            mock_settings.poster_encode_format = "webp"
            mock_settings.poster_encode_quality = 75
            mock_settings.poster_max_width = 0
            result = temp_cache_service.get_cached_poster(20007)

        assert result is not None
        cache_path, content_type = result
        assert cache_path.suffix == ".webp"
        assert content_type == "image/webp"
        files = list(temp_cache_service.cache_dir.glob("20007.*"))
        assert [f.suffix for f in files] == [".webp"]

    def test_save_poster_falls_back_to_original_on_encode_failure(self, temp_cache_service):
        """Test that an unencodable poster is stored as-is with its original extension."""
        with patch("app.services.poster_service.settings") as mock_settings:
            mock_settings.poster_encode_format = "webp"
            mock_settings.poster_encode_quality = 75
            mock_settings.poster_max_width = 0
            content = b"not a real image"
            cache_path = temp_cache_service.save_poster(20008, content, "image/jpeg")

        assert cache_path is not None
        assert cache_path.suffix == ".jpg"
        assert cache_path.read_bytes() == content

    def test_get_cached_poster_returns_unchanged_when_format_matches(self, temp_cache_service):
        """Test that a cache matching the target format is served without re-encoding."""
        with patch("app.services.poster_service.settings") as mock_settings:
            mock_settings.poster_encode_format = "webp"
            mock_settings.poster_encode_quality = 75
            mock_settings.poster_max_width = 0
            temp_cache_service.save_poster(20009, _make_image(200, 300), "image/png")
            result = temp_cache_service.get_cached_poster(20009)

        assert result is not None
        cache_path, content_type = result
        assert cache_path.suffix == ".webp"
        assert content_type == "image/webp"
        files = list(temp_cache_service.cache_dir.glob("20009.*"))
        assert [f.suffix for f in files] == [".webp"]
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
            mock_settings.poster_encode_format = "original"
            mock_settings.poster_encode_quality = 80
            mock_settings.poster_max_width = 0
            service = PosterCacheService()
            assert service.ttl_days == 100

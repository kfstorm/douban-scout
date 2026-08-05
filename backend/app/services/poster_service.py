"""Poster caching service for Douban Scout."""

import io
import logging
import mimetypes
from datetime import datetime, timedelta
from pathlib import Path
from typing import ClassVar

from PIL import Image

from app.config import settings

logger = logging.getLogger("douban.posters")

# Encode target -> (PIL save format, output content type)
_ENCODE_FORMATS: dict[str, tuple[str, str]] = {
    "webp": ("WEBP", "image/webp"),
    "avif": ("AVIF", "image/avif"),
    "jpeg": ("JPEG", "image/jpeg"),
}


class PosterCacheService:
    """Service for managing cached poster images."""

    CACHE_SUBDIR = "cache/posters"
    IMAGE_EXTENSIONS: ClassVar[set[str]] = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif",
        ".avif",
        ".svg",
    }

    def __init__(self, ttl_days: int | None = None) -> None:
        """Initialize the poster cache service.

        Args:
            ttl_days: Cache TTL in days. If None, uses settings.poster_cache_ttl.
        """
        self.cache_dir = Path(settings.data_dir) / self.CACHE_SUBDIR
        self.ttl_days = ttl_days if ttl_days is not None else settings.poster_cache_ttl
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Poster cache directory: {self.cache_dir}")

    def _get_cache_path(self, movie_id: int, content_type: str) -> Path:
        """Generate cache file path for a movie poster.

        Args:
            movie_id: The movie/TV show ID
            content_type: The content type (e.g., "image/jpeg")

        Returns:
            Path to the cache file
        """
        extension = self._get_extension_from_content_type(content_type)
        return self.cache_dir / f"{movie_id}{extension}"

    def _get_extension_from_content_type(self, content_type: str) -> str:
        """Get file extension from content type.

        Args:
            content_type: The content type (e.g., "image/jpeg")

        Returns:
            File extension including the dot (e.g., ".jpg")
        """
        # Map common content types to extensions
        extension_map = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/gif": ".gif",
            "image/avif": ".avif",
            "image/svg+xml": ".svg",
        }

        # Normalize content type (remove charset, etc.)
        content_type = content_type.split(";", maxsplit=1)[0].strip().lower()

        if content_type in extension_map:
            return extension_map[content_type]

        # Try to guess from mimetypes module
        ext = mimetypes.guess_extension(content_type)
        if ext:
            return ext

        # Default to .jpg if unknown
        return ".jpg"

    def _guess_content_type_from_extension(self, extension: str) -> str:
        """Guess content type from file extension.

        Args:
            extension: File extension (e.g., ".jpg")

        Returns:
            Content type (e.g., "image/jpeg")
        """
        extension = extension.lower()
        type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif",
            ".avif": "image/avif",
            ".svg": "image/svg+xml",
        }

        if extension in type_map:
            return type_map[extension]

        # Try mimetypes module
        content_type, _ = mimetypes.guess_type(f"file{extension}")
        if content_type:
            return content_type

        return "image/jpeg"  # Default

    def is_cache_valid(self, cache_path: Path) -> bool:
        """Check if a cached file is valid (exists and not expired).

        Args:
            cache_path: Path to the cached file

        Returns:
            True if cache is valid, False otherwise
        """
        if not cache_path.exists():
            return False

        if cache_path.stat().st_size == 0:
            logger.debug(f"Cache file is empty: {cache_path}")
            return False

        # Check TTL
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mtime

        if age > timedelta(days=self.ttl_days):
            logger.debug(f"Cache expired for {cache_path} (age: {age.days} days)")
            return False

        return True

    def get_cached_poster(self, movie_id: int) -> tuple[Path, str] | None:
        """Get cached poster for a movie if available and valid.

        Args:
            movie_id: The movie/TV show ID

        Returns:
            Tuple of (cache_path, content_type) if cache hit, None otherwise
        """
        # Look for any file with this movie_id prefix
        pattern = f"{movie_id}.*"
        matching_files = list(self.cache_dir.glob(pattern))

        for cache_path in matching_files:
            if self.is_cache_valid(cache_path):
                content_type = self._guess_content_type_from_extension(cache_path.suffix)
                expected_extension = self._expected_extension()
                if expected_extension and cache_path.suffix.lower() != expected_extension:
                    # Lazy re-encode: cached file uses an outdated format. If anything
                    # fails here, fall back to serving the current file without crashing.
                    logger.debug(f"Cache format mismatch for movie {movie_id}: {cache_path}")
                    try:
                        encoded, encoded_type = self._encode_image(
                            cache_path.read_bytes(), content_type
                        )
                        if (
                            self._get_extension_from_content_type(encoded_type)
                            != cache_path.suffix.lower()
                        ):
                            new_path = self._get_cache_path(movie_id, encoded_type)
                            new_path.write_bytes(encoded)
                            self._remove_other_versions(movie_id, keep=new_path)
                            logger.debug(f"Re-encoded cache for movie {movie_id}: {new_path}")
                            return new_path, encoded_type
                    except OSError as e:
                        logger.error(f"Failed to re-encode cache for movie {movie_id}: {e}")

                logger.debug(f"Cache hit for movie {movie_id}: {cache_path}")
                return cache_path, content_type

        return None

    def save_poster(self, movie_id: int, content: bytes, content_type: str) -> Path | None:
        """Save a poster image to cache.

        Args:
            movie_id: The movie/TV show ID
            content: The image content bytes
            content_type: The content type (e.g., "image/jpeg")

        Returns:
            Path to the saved cache file, or None if save failed
        """
        try:
            encoded, encoded_type = self._encode_image(content, content_type)
            cache_path = self._get_cache_path(movie_id, encoded_type)

            # Remove any existing cached files for this movie in other formats
            self._remove_other_versions(movie_id, keep=cache_path)

            # Write new cache file
            cache_path.write_bytes(encoded)
            logger.debug(f"Saved poster to cache: {cache_path} ({len(encoded)} bytes)")

            return cache_path
        except OSError as e:
            logger.error(f"Failed to save poster to cache: {e}")
            return None

    def _remove_other_versions(self, movie_id: int, keep: Path) -> None:
        """Remove cached files for a movie that use a different format.

        Args:
            movie_id: The movie/TV show ID.
            keep: The cache file to retain.
        """
        for old_file in self.cache_dir.glob(f"{movie_id}.*"):
            if old_file == keep:
                continue
            try:
                old_file.unlink()
                logger.debug(f"Removed old cache: {old_file}")
            except OSError as e:
                logger.error(f"Failed to remove {old_file}: {e}")

    def _expected_extension(self) -> str | None:
        """Return the file extension for the configured target format.

        Returns:
            The extension including the dot (e.g., ".webp"), or None when the
            original format is used.
        """
        target = settings.poster_encode_format
        if target == "original":
            return None
        return self._get_extension_from_content_type(_ENCODE_FORMATS[target][1])

    def _encode_image(self, content: bytes, content_type: str) -> tuple[bytes, str]:
        """Re-encode image bytes to the configured format, quality and max width.

        Args:
            content: The original image bytes.
            content_type: The original content type (e.g., "image/jpeg").

        Returns:
            A tuple of (encoded_bytes, content_type). Falls back to the original
            bytes and content type when encoding is disabled or fails.
        """
        target = settings.poster_encode_format
        if target == "original":
            return content, content_type

        try:
            save_format, output_type = _ENCODE_FORMATS[target]
            image = Image.open(io.BytesIO(content))
            max_width = settings.poster_max_width
            if max_width and image.width > max_width:
                ratio = max_width / image.width
                new_size = (max_width, max(1, round(image.height * ratio)))
                encoded_image = image.resize(new_size, Image.Resampling.LANCZOS)
            else:
                encoded_image = image

            output = io.BytesIO()
            if target == "jpeg":
                # JPEG does not support alpha; flatten to RGB first
                to_save = (
                    encoded_image.convert("RGB")
                    if encoded_image.mode not in ("RGB", "L")
                    else encoded_image
                )
            else:
                to_save = encoded_image
            to_save.save(output, format=save_format, quality=settings.poster_encode_quality)
            return output.getvalue(), output_type
        except Exception:
            # Resilience requirement: a poster request must never fail because
            # re-encoding failed, so fall back to the original bytes.
            logger.exception("Failed to re-encode poster image, storing original")
            return content, content_type

    def clear_cache(self) -> int:
        """Clear all cached posters.

        Returns:
            Number of files removed
        """
        count = 0
        for cache_file in self.cache_dir.glob("*"):
            if cache_file.is_file():
                try:
                    cache_file.unlink()
                    count += 1
                except OSError as e:
                    logger.error(f"Failed to remove {cache_file}: {e}")

        logger.info(f"Cleared {count} cached posters")
        return count

    def clear_expired_cache(self) -> int:
        """Remove cached posters whose age exceeds the configured TTL.

        Returns:
            Number of expired files removed
        """
        count = 0
        expiration = timedelta(days=self.ttl_days)
        now = datetime.now()

        for cache_file in self.cache_dir.glob("*"):
            if (
                not cache_file.is_file()
                or not cache_file.stem.isdigit()
                or cache_file.suffix.lower() not in self.IMAGE_EXTENSIONS
            ):
                continue

            try:
                age = now - datetime.fromtimestamp(cache_file.stat().st_mtime)
                if age <= expiration:
                    continue

                cache_file.unlink()
                count += 1
                logger.debug(f"Removed expired cache: {cache_file}")
            except OSError as e:
                logger.exception(f"Failed to remove expired cache {cache_file}: {e}")

        logger.info(f"Cleared {count} expired cached posters")
        return count


# Global instance
poster_cache_service = PosterCacheService()

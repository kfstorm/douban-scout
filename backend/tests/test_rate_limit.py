"""Tests for API rate limiting."""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.limiter import limiter


class TestRateLimiting:
    """Tests for API rate limiting."""

    @pytest.fixture(autouse=True)
    def enable_limiter(self):
        """Enable limiter for this test class."""
        was_enabled = limiter.enabled
        limiter.enabled = True
        yield
        limiter.enabled = was_enabled

    def test_rate_limit_movies(self, client: TestClient):
        """Test rate limiting on movies endpoint."""
        # The limit is 30/minute by default. We make 31 requests.
        # Note: In tests, the limit might be shared if not isolated.
        # But here each test starts fresh.
        limit = 30

        for _ in range(limit):
            response = client.get("/api/movies")
            assert response.status_code == 200

        response = client.get("/api/movies")
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.text

    def test_rate_limit_config_loading(self, monkeypatch):
        """Test that rate limits are loaded from environment variables."""
        monkeypatch.setenv("RATE_LIMIT_STATS", "5/minute")
        monkeypatch.setenv("DATA_DIR", "/tmp/test_data")

        # Create a new settings instance to verify loading
        new_settings = Settings()
        assert new_settings.rate_limit_stats == "5/minute"
        assert new_settings.data_dir == "/tmp/test_data"

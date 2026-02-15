import pytest

from app.services.import_service import ImportService


@pytest.fixture
def import_service():
    """Get ImportService instance."""
    ImportService._instance = None
    return ImportService()


class TestMetadataExtraction:
    """Tests for metadata extraction logic in ImportService."""

    def test_extract_genres_simple(self, import_service):
        """Test simple genre extraction."""
        s = "剧情 / 动作 / 犯罪"
        genres = import_service._extract_metadata_from_string(s, is_genre=True)
        assert genres == {"剧情", "动作", "犯罪"}

    def test_extract_regions_simple(self, import_service):
        """Test simple region extraction."""
        s = "美国 / 法国 / 日本"
        regions = import_service._extract_metadata_from_string(s, is_genre=False)
        assert regions == {"美国", "法国", "日本"}

    def test_extract_mixed_languages(self, import_service):
        """Test extraction from strings with mixed languages (Chinese prioritized)."""
        s = "Canada 加拿大 / France 法国"
        regions = import_service._extract_metadata_from_string(s, is_genre=False)
        assert regions == {"加拿大", "法国"}

    def test_context_aware_parsing(self, import_service):
        """Test parsing of card_subtitle-like strings."""
        s = "1994 / 美国 法国 / 剧情 犯罪"
        # Test regions
        regions = import_service._extract_metadata_from_string(s, is_genre=False)
        assert regions == {"美国", "法国"}

        # Test genres
        genres = import_service._extract_metadata_from_string(s, is_genre=True)
        assert genres == {"剧情", "犯罪"}

    def test_complex_delimiters(self, import_service):
        """Test handling of different delimiters."""
        s = "美国,法国|日本，英国、德国"
        regions = import_service._extract_metadata_from_string(s, is_genre=False)
        assert regions == {"美国", "法国", "日本", "英国", "德国"}

    def test_no_false_positives_from_titles(self, import_service):
        """Test that parts of titles don't trigger false positives if they don't match exactly."""
        # "美国" is a region. "美国往事" is a title.
        # With word boundary logic (\b), "美国" should NOT match "美国往事"
        s = "美国往事"
        regions = import_service._extract_metadata_from_string(s, is_genre=False)
        assert "美国" not in regions

    def test_congo_kinshasa_case(self, import_service):
        """Test handling of regions with parentheses like 刚果（金）."""
        s = "1994 / 刚果（金） / 剧情"
        regions = import_service._extract_metadata_from_string(s, is_genre=False)
        assert "刚果（金）" in regions
        assert "金" not in regions

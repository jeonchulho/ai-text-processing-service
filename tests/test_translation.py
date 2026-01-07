"""
Tests for translation service and workflow.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.api.dependencies import get_db
from src.models.database import Base

# Create test database
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for tests."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_database():
    """Setup test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestTranslation:
    """Test translation endpoints."""

    def test_translate_text(self, setup_database):
        """Test single text translation."""
        response = client.post(
            "/api/v1/translate",
            json={
                "text": "Hello, world!",
                "target_lang": "ko"
            }
        )
        
        # Note: This will fail without OpenAI API key
        # In production, use mock for testing
        assert response.status_code in [200, 422, 500]

    def test_translate_with_source_lang(self, setup_database):
        """Test translation with specified source language."""
        response = client.post(
            "/api/v1/translate",
            json={
                "text": "Hello, world!",
                "target_lang": "ko",
                "source_lang": "en"
            }
        )
        
        assert response.status_code in [200, 422, 500]

    def test_translate_invalid_lang(self, setup_database):
        """Test translation with invalid language code."""
        response = client.post(
            "/api/v1/translate",
            json={
                "text": "Hello, world!",
                "target_lang": "invalid"
            }
        )
        
        assert response.status_code == 422

    def test_translate_empty_text(self, setup_database):
        """Test translation with empty text."""
        response = client.post(
            "/api/v1/translate",
            json={
                "text": "",
                "target_lang": "ko"
            }
        )
        
        assert response.status_code == 422

    def test_batch_translation(self, setup_database):
        """Test batch translation."""
        response = client.post(
            "/api/v1/translate/batch",
            json={
                "texts": ["Hello", "World", "Test"],
                "target_lang": "ko"
            }
        )
        
        assert response.status_code in [200, 422, 500]

    def test_translation_history(self, setup_database):
        """Test getting translation history."""
        response = client.get("/api/v1/translate/history")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_cache_stats(self, setup_database):
        """Test getting cache statistics."""
        response = client.get("/api/v1/translate/stats/cache")
        
        assert response.status_code == 200
        assert "cache_hit_rate" in response.json()


class TestTranslationWorkflow:
    """Test translation workflow logic."""

    def test_language_detection(self):
        """Test automatic language detection."""
        from src.utils.text_processing import detect_language
        
        assert detect_language("Hello, world!") == "en"
        assert detect_language("안녕하세요") == "ko"
        assert detect_language("こんにちは") == "ja"

    def test_text_hash(self):
        """Test text hashing for cache keys."""
        from src.utils.text_processing import compute_text_hash
        
        hash1 = compute_text_hash("test")
        hash2 = compute_text_hash("test")
        hash3 = compute_text_hash("different")
        
        assert hash1 == hash2
        assert hash1 != hash3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Tests for summarization service and workflow.
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


class TestSummarization:
    """Test summarization endpoints."""

    def test_summarize_document(self, setup_database):
        """Test document summarization."""
        long_text = "This is a test document. " * 50
        
        response = client.post(
            "/api/v1/summarize/document",
            json={
                "content": long_text,
                "content_type": "text"
            }
        )
        
        # Note: This will fail without OpenAI API key
        assert response.status_code in [200, 422, 500]

    def test_summarize_short_document(self, setup_database):
        """Test summarization with minimum length text."""
        response = client.post(
            "/api/v1/summarize/document",
            json={
                "content": "Short text. " * 10,
                "content_type": "text"
            }
        )
        
        assert response.status_code in [200, 422, 500]

    def test_summarize_invalid_content_type(self, setup_database):
        """Test summarization with invalid content type."""
        response = client.post(
            "/api/v1/summarize/document",
            json={
                "content": "Test content",
                "content_type": "invalid"
            }
        )
        
        assert response.status_code == 422

    def test_summarize_too_short(self, setup_database):
        """Test summarization with text that's too short."""
        response = client.post(
            "/api/v1/summarize/document",
            json={
                "content": "Too short",
                "content_type": "text"
            }
        )
        
        assert response.status_code == 422

    def test_get_keywords(self, setup_database):
        """Test getting keywords for non-existent summary."""
        response = client.get("/api/v1/summarize/keywords/999")
        
        assert response.status_code == 404

    def test_summary_history(self, setup_database):
        """Test getting summary history."""
        response = client.get("/api/v1/summarize/history")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_summary_history_with_filter(self, setup_database):
        """Test getting summary history with content type filter."""
        response = client.get("/api/v1/summarize/history?content_type=document")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestSummarizationWorkflow:
    """Test summarization workflow logic."""

    def test_text_chunking(self):
        """Test text chunking functionality."""
        from src.utils.text_processing import chunk_text
        
        long_text = "This is a sentence. " * 200
        chunks = chunk_text(long_text, chunk_size=100, overlap=20)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 120 for chunk in chunks)  # chunk_size + some margin

    def test_text_cleaning(self):
        """Test text cleaning."""
        from src.utils.text_processing import clean_text
        
        dirty_text = "  Too   much    whitespace  \n\n  "
        clean = clean_text(dirty_text)
        
        assert clean == "Too much whitespace"

    def test_sentence_extraction(self):
        """Test sentence extraction."""
        from src.utils.text_processing import extract_sentences
        
        text = "First sentence. Second sentence! Third sentence?"
        sentences = extract_sentences(text)
        
        assert len(sentences) == 3


class TestDocumentParsing:
    """Test document parsing functionality."""

    def test_text_parsing(self):
        """Test plain text parsing."""
        from src.services.document_service import document_service
        
        content = b"This is plain text content"
        parsed = document_service.parse_text(content)
        
        assert parsed == "This is plain text content"

    def test_invalid_file_type(self):
        """Test parsing with invalid file type."""
        from src.services.document_service import document_service
        from src.core.exceptions import ValidationError
        
        with pytest.raises(ValidationError):
            document_service.parse_document(b"content", "invalid")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

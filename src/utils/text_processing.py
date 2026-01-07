"""
Text processing utilities.

This module provides utility functions for text chunking,
cleaning, and other text processing operations.
"""

import re
import hashlib
from typing import List, Optional
import structlog

logger = structlog.get_logger(__name__)


def clean_text(text: str) -> str:
    """
    Clean and normalize text.

    Args:
        text: Text to clean

    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove leading/trailing whitespace
    text = text.strip()

    return text


def compute_text_hash(text: str) -> str:
    """
    Compute SHA-256 hash of text for caching.

    Args:
        text: Text to hash

    Returns:
        Hex digest of hash
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 100
) -> List[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: Text to chunk
        chunk_size: Maximum characters per chunk
        overlap: Number of overlapping characters between chunks

    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings
            sentence_end = max(
                text.rfind('. ', start, end),
                text.rfind('! ', start, end),
                text.rfind('? ', start, end),
                text.rfind('\n', start, end)
            )

            if sentence_end > start:
                end = sentence_end + 1

        chunks.append(text[start:end].strip())
        start = end - overlap if end < len(text) else end

    return chunks


def chunk_text_by_tokens(
    text: str,
    max_tokens: int = 500,
    overlap_tokens: int = 50
) -> List[str]:
    """
    Split text into chunks by approximate token count.

    Args:
        text: Text to chunk
        max_tokens: Maximum tokens per chunk (approximate)
        overlap_tokens: Overlapping tokens between chunks

    Returns:
        List of text chunks
    """
    # Rough approximation: 1 token ≈ 4 characters
    chunk_size = max_tokens * 4
    overlap_size = overlap_tokens * 4

    return chunk_text(text, chunk_size, overlap_size)


def extract_sentences(text: str) -> List[str]:
    """
    Extract sentences from text.

    Args:
        text: Text to extract sentences from

    Returns:
        List of sentences
    """
    # Simple sentence splitting
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def truncate_text(
    text: str,
    max_length: int,
    suffix: str = "..."
) -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def detect_language(text: str) -> Optional[str]:
    """
    Detect language of text (simple heuristic).

    Args:
        text: Text to analyze

    Returns:
        Language code ('ko', 'en', 'ja', 'zh') or None
    """
    # Korean: Hangul characters
    if re.search(r'[ㄱ-ㅎ가-힣]', text):
        return 'ko'

    # Japanese: Hiragana or Katakana
    if re.search(r'[ぁ-ゔァ-ヴー]', text):
        return 'ja'

    # Chinese: CJK characters (excluding Japanese Kanji)
    if re.search(r'[\u4e00-\u9fff]', text):
        # If no Japanese-specific characters, assume Chinese
        if not re.search(r'[ぁ-ゔァ-ヴー]', text):
            return 'zh'

    # Default to English
    return 'en'


def format_chat_messages(messages: List[dict]) -> str:
    """
    Format chat messages for display or summarization.

    Args:
        messages: List of message dictionaries with 'sender_name' and 'message'

    Returns:
        Formatted chat text
    """
    formatted = []
    for msg in messages:
        sender = msg.get('sender_name', 'Unknown')
        content = msg.get('message', '')
        timestamp = msg.get('timestamp', '')

        if timestamp:
            formatted.append(f"[{timestamp}] {sender}: {content}")
        else:
            formatted.append(f"{sender}: {content}")

    return "\n".join(formatted)


def extract_metadata_from_text(text: str) -> dict:
    """
    Extract basic metadata from text.

    Args:
        text: Text to analyze

    Returns:
        Dictionary with metadata (length, language, etc.)
    """
    return {
        "length": len(text),
        "word_count": len(text.split()),
        "language": detect_language(text),
        "has_urls": bool(re.search(r'https?://', text)),
        "has_emails": bool(re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text))
    }

"""
LLM client for OpenAI API interactions.

This module provides a wrapper around OpenAI's API for text generation,
embeddings, and other LLM operations with error handling and retries.
"""

from typing import List, Optional, Dict, Any
import time
import structlog
from openai import OpenAI, OpenAIError
import tiktoken

from src.core.config import settings
from src.core.exceptions import LLMError

logger = structlog.get_logger(__name__)


class LLMClient:
    """OpenAI LLM client wrapper with utilities."""

    def __init__(self):
        """Initialize OpenAI client."""
        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not configured")
            self.client = None
        else:
            try:
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
                self.model = settings.OPENAI_MODEL
                self.embedding_model = settings.OPENAI_EMBEDDING_MODEL
                logger.info("LLM client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize LLM client: {e}")
                raise LLMError(f"LLM initialization failed: {e}")

    def _ensure_client(self):
        """Ensure client is initialized."""
        if self.client is None:
            raise LLMError("OpenAI client not initialized. Check API key.")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Generate chat completion.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            model: Model to use (defaults to configured model)

        Returns:
            Generated text response
        """
        self._ensure_client()

        try:
            response = self.client.chat.completions.create(
                model=model or self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            return response.choices[0].message.content

        except OpenAIError as e:
            logger.error(f"OpenAI chat completion error: {e}")
            raise LLMError(f"Chat completion failed: {e}")

    def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ):
        """
        Generate streaming chat completion.

        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            model: Model to use

        Yields:
            Text chunks as they are generated
        """
        self._ensure_client()

        try:
            stream = self.client.chat.completions.create(
                model=model or self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except OpenAIError as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise LLMError(f"Streaming completion failed: {e}")

    def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        self._ensure_client()

        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )

            return response.data[0].embedding

        except OpenAIError as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise LLMError(f"Embedding generation failed: {e}")

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        self._ensure_client()

        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )

            return [item.embedding for item in response.data]

        except OpenAIError as e:
            logger.error(f"OpenAI batch embedding error: {e}")
            raise LLMError(f"Batch embedding generation failed: {e}")

    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Count tokens in text for a given model.

        Args:
            text: Text to count tokens for
            model: Model name (defaults to configured model)

        Returns:
            Number of tokens
        """
        try:
            encoding = tiktoken.encoding_for_model(model or self.model)
            return len(encoding.encode(text))
        except Exception as e:
            logger.warning(f"Token counting error: {e}, using approximation")
            # Fallback: rough approximation
            return len(text) // 4

    def translate_text(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None
    ) -> str:
        """
        Translate text using LLM.

        Args:
            text: Text to translate
            target_lang: Target language code
            source_lang: Source language code (optional)

        Returns:
            Translated text
        """
        lang_names = {
            "ko": "Korean",
            "en": "English",
            "ja": "Japanese",
            "zh": "Chinese"
        }

        target_name = lang_names.get(target_lang, target_lang)

        if source_lang:
            source_name = lang_names.get(source_lang, source_lang)
            prompt = f"Translate the following text from {source_name} to {target_name}. Provide only the translation without any explanation:\n\n{text}"
        else:
            prompt = f"Translate the following text to {target_name}. Provide only the translation without any explanation:\n\n{text}"

        messages = [
            {"role": "system", "content": "You are a professional translator. Provide accurate, natural translations."},
            {"role": "user", "content": prompt}
        ]

        return self.chat_completion(messages, temperature=0.3)

    def summarize_text(
        self,
        text: str,
        max_length: Optional[int] = None
    ) -> str:
        """
        Summarize text using LLM.

        Args:
            text: Text to summarize
            max_length: Maximum summary length in words

        Returns:
            Summary text
        """
        prompt = f"Summarize the following text concisely"
        if max_length:
            prompt += f" in about {max_length} words"
        prompt += f":\n\n{text}"

        messages = [
            {"role": "system", "content": "You are a helpful assistant that creates clear, concise summaries."},
            {"role": "user", "content": prompt}
        ]

        return self.chat_completion(messages, temperature=0.5)

    def extract_keywords(
        self,
        text: str,
        num_keywords: int = 5
    ) -> List[str]:
        """
        Extract keywords from text.

        Args:
            text: Text to extract keywords from
            num_keywords: Number of keywords to extract

        Returns:
            List of keywords
        """
        prompt = f"Extract the {num_keywords} most important keywords from the following text. Return them as a comma-separated list:\n\n{text}"

        messages = [
            {"role": "system", "content": "You are a helpful assistant that extracts key information."},
            {"role": "user", "content": prompt}
        ]

        response = self.chat_completion(messages, temperature=0.3)

        # Parse comma-separated keywords
        keywords = [kw.strip() for kw in response.split(",")]
        return keywords[:num_keywords]

    def detect_schedule(self, text: str) -> Dict[str, Any]:
        """
        Detect schedule information from text.

        Args:
            text: Text to analyze for schedule information

        Returns:
            Dictionary with detected schedule information
        """
        prompt = f"""Analyze the following text and extract any schedule/event information.
Return a JSON object with these fields (use null if not found):
- has_schedule: boolean
- title: string
- date: string (YYYY-MM-DD format)
- time: string (HH:MM format)
- location: string
- attendees: array of strings

Text: {text}"""

        messages = [
            {"role": "system", "content": "You are a helpful assistant that extracts schedule information. Always respond with valid JSON."},
            {"role": "user", "content": prompt}
        ]

        response = self.chat_completion(messages, temperature=0.3)

        # Parse JSON response
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"has_schedule": False}


# Global LLM client instance
llm_client = LLMClient()

"""
Translation service.

This service provides high-level translation operations,
integrating the workflow with database persistence.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
import structlog

from src.workflows.translation_workflow import translation_workflow, TranslationState
from src.repositories.translation_repository import TranslationRepository
from src.utils.text_processing import detect_language
from src.core.exceptions import TranslationError
from src.core.config import settings

logger = structlog.get_logger(__name__)


class TranslationService:
    """Service for translation operations."""

    def __init__(self, db: Session):
        """
        Initialize service with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.repository = TranslationRepository(db)

    async def translate(
        self,
        user_id: int,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None
    ) -> dict:
        """
        Translate text.

        Args:
            user_id: User ID
            text: Text to translate
            target_lang: Target language code
            source_lang: Source language code (optional)

        Returns:
            Dictionary with translation result
        """
        try:
            # Validate feature is enabled
            if not settings.ENABLE_TRANSLATION:
                raise TranslationError("Translation feature is disabled")

            # Auto-detect source language if not provided
            if not source_lang:
                source_lang = detect_language(text)

            # Run workflow
            initial_state: TranslationState = {
                "source_text": text,
                "target_lang": target_lang,
                "source_lang": source_lang,
                "translated_text": None,
                "cached": False,
                "error": None
            }

            result = translation_workflow.invoke(initial_state)

            # Check for errors
            if result.get("error"):
                raise TranslationError(result["error"])

            # Save to database
            translation_record = self.repository.create(
                user_id=user_id,
                source_text=text,
                translated_text=result["translated_text"],
                source_lang=result["source_lang"],
                target_lang=target_lang,
                cache_hit=result["cached"],
                vector_stored=True,
                model_used=settings.OPENAI_MODEL
            )

            logger.info(f"Translation completed: {translation_record.id}")

            return {
                "id": translation_record.id,
                "source_text": text,
                "translated_text": result["translated_text"],
                "source_lang": result["source_lang"],
                "target_lang": target_lang,
                "cache_hit": result["cached"],
                "created_at": translation_record.created_at
            }

        except TranslationError:
            raise
        except Exception as e:
            logger.error(f"Translation service error: {e}")
            raise TranslationError(f"Translation failed: {e}")

    async def translate_batch(
        self,
        user_id: int,
        texts: List[str],
        target_lang: str,
        source_lang: Optional[str] = None
    ) -> List[dict]:
        """
        Translate multiple texts.

        Args:
            user_id: User ID
            texts: List of texts to translate
            target_lang: Target language code
            source_lang: Source language code (optional)

        Returns:
            List of translation results
        """
        try:
            results = []

            for text in texts:
                try:
                    result = await self.translate(
                        user_id=user_id,
                        text=text,
                        target_lang=target_lang,
                        source_lang=source_lang
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"Batch translation error for text: {e}")
                    results.append({
                        "error": str(e),
                        "source_text": text
                    })

            return results

        except Exception as e:
            logger.error(f"Batch translation service error: {e}")
            raise TranslationError(f"Batch translation failed: {e}")

    def get_history(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[dict]:
        """
        Get user's translation history.

        Args:
            user_id: User ID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of translation records
        """
        try:
            translations = self.repository.get_user_history(
                user_id=user_id,
                limit=limit,
                offset=offset
            )

            return [
                {
                    "id": t.id,
                    "source_text": t.source_text,
                    "translated_text": t.translated_text,
                    "source_lang": t.source_lang,
                    "target_lang": t.target_lang,
                    "cache_hit": t.cache_hit,
                    "created_at": t.created_at
                }
                for t in translations
            ]

        except Exception as e:
            logger.error(f"History retrieval error: {e}")
            raise TranslationError(f"Failed to retrieve history: {e}")

    def get_cache_stats(self, user_id: int, days: int = 7) -> dict:
        """
        Get cache statistics for user.

        Args:
            user_id: User ID
            days: Days to look back

        Returns:
            Dictionary with cache statistics
        """
        try:
            hit_rate = self.repository.get_cache_hit_rate(user_id, days)

            return {
                "cache_hit_rate": hit_rate,
                "days": days
            }

        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"cache_hit_rate": 0.0, "days": days}

"""
Translation repository for database operations.

This module handles all database operations related to translations,
including CRUD operations and querying translation history.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
import structlog

from src.models.database import Translation, User
from src.core.exceptions import DatabaseError, NotFoundError

logger = structlog.get_logger(__name__)


class TranslationRepository:
    """Repository for translation database operations."""

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create(
        self,
        user_id: int,
        source_text: str,
        translated_text: str,
        source_lang: str,
        target_lang: str,
        cache_hit: bool = False,
        vector_stored: bool = False,
        model_used: Optional[str] = None,
        token_count: Optional[int] = None
    ) -> Translation:
        """
        Create a new translation record.

        Args:
            user_id: User ID
            source_text: Original text
            translated_text: Translated text
            source_lang: Source language code
            target_lang: Target language code
            cache_hit: Whether result was from cache
            vector_stored: Whether embedding was stored
            model_used: LLM model used
            token_count: Number of tokens used

        Returns:
            Created Translation object
        """
        try:
            translation = Translation(
                user_id=user_id,
                source_text=source_text,
                translated_text=translated_text,
                source_lang=source_lang,
                target_lang=target_lang,
                cache_hit=cache_hit,
                vector_stored=vector_stored,
                model_used=model_used,
                token_count=token_count
            )

            self.db.add(translation)
            self.db.commit()
            self.db.refresh(translation)

            logger.info(f"Created translation record: {translation.id}")
            return translation

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create translation: {e}")
            raise DatabaseError(f"Translation creation failed: {e}")

    def get_by_id(self, translation_id: int) -> Optional[Translation]:
        """
        Get translation by ID.

        Args:
            translation_id: Translation ID

        Returns:
            Translation object or None
        """
        try:
            return self.db.query(Translation).filter(
                Translation.id == translation_id
            ).first()
        except Exception as e:
            logger.error(f"Failed to get translation {translation_id}: {e}")
            raise DatabaseError(f"Translation retrieval failed: {e}")

    def get_user_history(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Translation]:
        """
        Get user's translation history.

        Args:
            user_id: User ID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of Translation objects
        """
        try:
            return self.db.query(Translation).filter(
                Translation.user_id == user_id
            ).order_by(
                desc(Translation.created_at)
            ).limit(limit).offset(offset).all()

        except Exception as e:
            logger.error(f"Failed to get user history: {e}")
            raise DatabaseError(f"History retrieval failed: {e}")

    def get_recent_by_language_pair(
        self,
        user_id: int,
        source_lang: str,
        target_lang: str,
        hours: int = 24,
        limit: int = 10
    ) -> List[Translation]:
        """
        Get recent translations for a language pair.

        Args:
            user_id: User ID
            source_lang: Source language code
            target_lang: Target language code
            hours: Hours to look back
            limit: Maximum number of results

        Returns:
            List of Translation objects
        """
        try:
            since = datetime.utcnow() - timedelta(hours=hours)

            return self.db.query(Translation).filter(
                Translation.user_id == user_id,
                Translation.source_lang == source_lang,
                Translation.target_lang == target_lang,
                Translation.created_at >= since
            ).order_by(
                desc(Translation.created_at)
            ).limit(limit).all()

        except Exception as e:
            logger.error(f"Failed to get recent translations: {e}")
            raise DatabaseError(f"Recent translations retrieval failed: {e}")

    def get_cache_hit_rate(
        self,
        user_id: int,
        days: int = 7
    ) -> float:
        """
        Calculate cache hit rate for user.

        Args:
            user_id: User ID
            days: Days to look back

        Returns:
            Cache hit rate (0.0 to 1.0)
        """
        try:
            since = datetime.utcnow() - timedelta(days=days)

            total = self.db.query(Translation).filter(
                Translation.user_id == user_id,
                Translation.created_at >= since
            ).count()

            if total == 0:
                return 0.0

            cache_hits = self.db.query(Translation).filter(
                Translation.user_id == user_id,
                Translation.created_at >= since,
                Translation.cache_hit == True
            ).count()

            return cache_hits / total

        except Exception as e:
            logger.error(f"Failed to calculate cache hit rate: {e}")
            return 0.0

    def delete(self, translation_id: int) -> bool:
        """
        Delete a translation record.

        Args:
            translation_id: Translation ID to delete

        Returns:
            True if deleted successfully
        """
        try:
            translation = self.get_by_id(translation_id)
            if not translation:
                raise NotFoundError(f"Translation {translation_id} not found")

            self.db.delete(translation)
            self.db.commit()

            logger.info(f"Deleted translation: {translation_id}")
            return True

        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete translation: {e}")
            raise DatabaseError(f"Translation deletion failed: {e}")

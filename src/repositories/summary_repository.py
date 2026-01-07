"""
Summary repository for database operations.

This module handles all database operations related to summaries,
including CRUD operations and querying summary history.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
import structlog

from src.models.database import Summary
from src.core.exceptions import DatabaseError, NotFoundError

logger = structlog.get_logger(__name__)


class SummaryRepository:
    """Repository for summary database operations."""

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
        content_type: str,
        original_content: str,
        summary_text: str,
        keywords: Optional[List[str]] = None,
        chunk_count: Optional[int] = None,
        model_used: Optional[str] = None,
        token_count: Optional[int] = None,
        processing_time: Optional[float] = None
    ) -> Summary:
        """
        Create a new summary record.

        Args:
            user_id: User ID
            content_type: Type of content (chat, message, document)
            original_content: Original text content
            summary_text: Generated summary
            keywords: Extracted keywords
            chunk_count: Number of chunks processed
            model_used: LLM model used
            token_count: Number of tokens used
            processing_time: Processing time in seconds

        Returns:
            Created Summary object
        """
        try:
            summary = Summary(
                user_id=user_id,
                content_type=content_type,
                original_content=original_content,
                summary_text=summary_text,
                keywords=keywords or [],
                chunk_count=chunk_count,
                model_used=model_used,
                token_count=token_count,
                processing_time=processing_time
            )

            self.db.add(summary)
            self.db.commit()
            self.db.refresh(summary)

            logger.info(f"Created summary record: {summary.id}")
            return summary

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create summary: {e}")
            raise DatabaseError(f"Summary creation failed: {e}")

    def get_by_id(self, summary_id: int) -> Optional[Summary]:
        """
        Get summary by ID.

        Args:
            summary_id: Summary ID

        Returns:
            Summary object or None
        """
        try:
            return self.db.query(Summary).filter(
                Summary.id == summary_id
            ).first()
        except Exception as e:
            logger.error(f"Failed to get summary {summary_id}: {e}")
            raise DatabaseError(f"Summary retrieval failed: {e}")

    def get_user_summaries(
        self,
        user_id: int,
        content_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Summary]:
        """
        Get user's summaries.

        Args:
            user_id: User ID
            content_type: Optional content type filter
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of Summary objects
        """
        try:
            query = self.db.query(Summary).filter(
                Summary.user_id == user_id
            )

            if content_type:
                query = query.filter(Summary.content_type == content_type)

            return query.order_by(
                desc(Summary.created_at)
            ).limit(limit).offset(offset).all()

        except Exception as e:
            logger.error(f"Failed to get user summaries: {e}")
            raise DatabaseError(f"Summaries retrieval failed: {e}")

    def get_recent_summaries(
        self,
        user_id: int,
        hours: int = 24,
        limit: int = 10
    ) -> List[Summary]:
        """
        Get recent summaries.

        Args:
            user_id: User ID
            hours: Hours to look back
            limit: Maximum number of results

        Returns:
            List of Summary objects
        """
        try:
            since = datetime.utcnow() - timedelta(hours=hours)

            return self.db.query(Summary).filter(
                Summary.user_id == user_id,
                Summary.created_at >= since
            ).order_by(
                desc(Summary.created_at)
            ).limit(limit).all()

        except Exception as e:
            logger.error(f"Failed to get recent summaries: {e}")
            raise DatabaseError(f"Recent summaries retrieval failed: {e}")

    def get_keywords_by_summary_id(self, summary_id: int) -> List[str]:
        """
        Get keywords for a summary.

        Args:
            summary_id: Summary ID

        Returns:
            List of keywords
        """
        try:
            summary = self.get_by_id(summary_id)
            if not summary:
                raise NotFoundError(f"Summary {summary_id} not found")

            return summary.keywords or []

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get keywords: {e}")
            raise DatabaseError(f"Keywords retrieval failed: {e}")

    def get_average_processing_time(
        self,
        user_id: int,
        content_type: Optional[str] = None,
        days: int = 7
    ) -> float:
        """
        Calculate average processing time.

        Args:
            user_id: User ID
            content_type: Optional content type filter
            days: Days to look back

        Returns:
            Average processing time in seconds
        """
        try:
            since = datetime.utcnow() - timedelta(days=days)

            query = self.db.query(Summary).filter(
                Summary.user_id == user_id,
                Summary.created_at >= since,
                Summary.processing_time.isnot(None)
            )

            if content_type:
                query = query.filter(Summary.content_type == content_type)

            summaries = query.all()

            if not summaries:
                return 0.0

            total_time = sum(s.processing_time for s in summaries if s.processing_time)
            return total_time / len(summaries)

        except Exception as e:
            logger.error(f"Failed to calculate average processing time: {e}")
            return 0.0

    def delete(self, summary_id: int) -> bool:
        """
        Delete a summary record.

        Args:
            summary_id: Summary ID to delete

        Returns:
            True if deleted successfully
        """
        try:
            summary = self.get_by_id(summary_id)
            if not summary:
                raise NotFoundError(f"Summary {summary_id} not found")

            self.db.delete(summary)
            self.db.commit()

            logger.info(f"Deleted summary: {summary_id}")
            return True

        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete summary: {e}")
            raise DatabaseError(f"Summary deletion failed: {e}")

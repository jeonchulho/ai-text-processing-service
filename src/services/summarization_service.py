"""
Summarization service.

This service provides high-level summarization operations,
integrating the workflow with database persistence.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
import time
import structlog

from src.workflows.summarization_workflow import summarization_workflow, SummarizationState
from src.repositories.summary_repository import SummaryRepository
from src.models.database import ChatMessage, DirectMessage
from src.utils.text_processing import format_chat_messages
from src.core.exceptions import SummarizationError, NotFoundError
from src.core.config import settings

logger = structlog.get_logger(__name__)


class SummarizationService:
    """Service for summarization operations."""

    def __init__(self, db: Session):
        """
        Initialize service with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.repository = SummaryRepository(db)

    async def summarize_chat(
        self,
        user_id: int,
        chat_id: str,
        limit: int = 100
    ) -> dict:
        """
        Summarize chat conversation.

        Args:
            user_id: User ID
            chat_id: Chat ID
            limit: Maximum number of messages to summarize

        Returns:
            Dictionary with summarization result
        """
        try:
            # Validate feature is enabled
            if not settings.ENABLE_SUMMARIZATION:
                raise SummarizationError("Summarization feature is disabled")

            # Load chat messages
            messages = self.db.query(ChatMessage).filter(
                ChatMessage.chat_id == chat_id
            ).order_by(ChatMessage.timestamp).limit(limit).all()

            if not messages:
                raise NotFoundError(f"No messages found for chat {chat_id}")

            # Format messages
            formatted_content = format_chat_messages([
                {
                    "sender_name": m.sender_name,
                    "message": m.message,
                    "timestamp": m.timestamp.strftime("%Y-%m-%d %H:%M")
                }
                for m in messages
            ])

            # Run summarization workflow
            result = await self._run_summarization(
                user_id=user_id,
                content=formatted_content,
                content_type="chat"
            )

            logger.info(f"Chat summarization completed: {result['id']}")
            return result

        except (SummarizationError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"Chat summarization error: {e}")
            raise SummarizationError(f"Chat summarization failed: {e}")

    async def summarize_message(
        self,
        user_id: int,
        message_id: int
    ) -> dict:
        """
        Summarize direct message.

        Args:
            user_id: User ID
            message_id: Message ID

        Returns:
            Dictionary with summarization result
        """
        try:
            # Validate feature is enabled
            if not settings.ENABLE_SUMMARIZATION:
                raise SummarizationError("Summarization feature is disabled")

            # Load message
            message = self.db.query(DirectMessage).filter(
                DirectMessage.id == message_id
            ).first()

            if not message:
                raise NotFoundError(f"Message {message_id} not found")

            # Prepare content
            content = f"Subject: {message.subject}\n\n{message.message}" if message.subject else message.message

            # Run summarization workflow
            result = await self._run_summarization(
                user_id=user_id,
                content=content,
                content_type="message"
            )

            logger.info(f"Message summarization completed: {result['id']}")
            return result

        except (SummarizationError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"Message summarization error: {e}")
            raise SummarizationError(f"Message summarization failed: {e}")

    async def summarize_document(
        self,
        user_id: int,
        content: str,
        content_type: str = "text"
    ) -> dict:
        """
        Summarize document content.

        Args:
            user_id: User ID
            content: Document content
            content_type: Type of content (text, pdf, docx)

        Returns:
            Dictionary with summarization result
        """
        try:
            # Validate feature is enabled
            if not settings.ENABLE_SUMMARIZATION:
                raise SummarizationError("Summarization feature is disabled")

            # Run summarization workflow
            result = await self._run_summarization(
                user_id=user_id,
                content=content,
                content_type="document"
            )

            logger.info(f"Document summarization completed: {result['id']}")
            return result

        except SummarizationError:
            raise
        except Exception as e:
            logger.error(f"Document summarization error: {e}")
            raise SummarizationError(f"Document summarization failed: {e}")

    async def _run_summarization(
        self,
        user_id: int,
        content: str,
        content_type: str
    ) -> dict:
        """
        Run summarization workflow and save results.

        Args:
            user_id: User ID
            content: Content to summarize
            content_type: Type of content

        Returns:
            Dictionary with summarization result
        """
        start_time = time.time()

        # Run workflow
        initial_state: SummarizationState = {
            "content": content,
            "content_type": content_type,
            "chunks": [],
            "chunk_summaries": [],
            "summary": None,
            "keywords": [],
            "error": None,
            "start_time": start_time
        }

        result = summarization_workflow.invoke(initial_state)

        # Check for errors
        if result.get("error"):
            raise SummarizationError(result["error"])

        processing_time = time.time() - start_time

        # Save to database
        summary_record = self.repository.create(
            user_id=user_id,
            content_type=content_type,
            original_content=content,
            summary_text=result["summary"],
            keywords=result["keywords"],
            chunk_count=len(result["chunks"]),
            model_used=settings.OPENAI_MODEL,
            processing_time=processing_time
        )

        return {
            "id": summary_record.id,
            "content_type": content_type,
            "summary_text": result["summary"],
            "keywords": result["keywords"],
            "chunk_count": len(result["chunks"]),
            "processing_time": processing_time,
            "created_at": summary_record.created_at
        }

    def get_summary(self, summary_id: int) -> dict:
        """
        Get summary by ID.

        Args:
            summary_id: Summary ID

        Returns:
            Dictionary with summary details
        """
        try:
            summary = self.repository.get_by_id(summary_id)

            if not summary:
                raise NotFoundError(f"Summary {summary_id} not found")

            return {
                "id": summary.id,
                "content_type": summary.content_type,
                "summary_text": summary.summary_text,
                "keywords": summary.keywords,
                "chunk_count": summary.chunk_count,
                "processing_time": summary.processing_time,
                "created_at": summary.created_at
            }

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Summary retrieval error: {e}")
            raise SummarizationError(f"Failed to retrieve summary: {e}")

    def get_keywords(self, summary_id: int) -> List[str]:
        """
        Get keywords for a summary.

        Args:
            summary_id: Summary ID

        Returns:
            List of keywords
        """
        try:
            return self.repository.get_keywords_by_summary_id(summary_id)

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Keywords retrieval error: {e}")
            raise SummarizationError(f"Failed to retrieve keywords: {e}")

    def get_user_summaries(
        self,
        user_id: int,
        content_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[dict]:
        """
        Get user's summaries.

        Args:
            user_id: User ID
            content_type: Optional content type filter
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of summary records
        """
        try:
            summaries = self.repository.get_user_summaries(
                user_id=user_id,
                content_type=content_type,
                limit=limit,
                offset=offset
            )

            return [
                {
                    "id": s.id,
                    "content_type": s.content_type,
                    "summary_text": s.summary_text,
                    "keywords": s.keywords,
                    "created_at": s.created_at
                }
                for s in summaries
            ]

        except Exception as e:
            logger.error(f"Summaries retrieval error: {e}")
            raise SummarizationError(f"Failed to retrieve summaries: {e}")

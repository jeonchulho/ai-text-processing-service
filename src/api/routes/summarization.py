"""
Summarization API routes.

This module provides REST API endpoints for summarization operations.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import structlog

from src.api.dependencies import get_db, get_current_user_optional
from src.models.schemas import (
    ChatSummarizationRequest,
    MessageSummarizationRequest,
    DocumentSummarizationRequest,
    SummaryResponse,
    ErrorResponse
)
from src.models.database import User
from src.services.summarization_service import SummarizationService
from src.core.exceptions import SummarizationError, NotFoundError

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/summarize", tags=["summarization"])


@router.post(
    "/chat",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def summarize_chat(
    request: ChatSummarizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Summarize chat conversation.

    - **chat_id**: Chat ID to summarize
    - **limit**: Maximum number of messages to include (10-1000)

    Returns summary with extracted keywords.
    """
    try:
        service = SummarizationService(db)
        result = await service.summarize_chat(
            user_id=current_user.id,
            chat_id=request.chat_id,
            limit=request.limit
        )

        return SummaryResponse(**result)

    except NotFoundError as e:
        logger.error(f"Chat not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except SummarizationError as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in chat summarization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Summarization service error"
        )


@router.post(
    "/message",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse}
    }
)
async def summarize_message(
    request: MessageSummarizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Summarize direct message (쪽지).

    - **message_id**: Message ID to summarize

    Returns summary with extracted keywords.
    """
    try:
        service = SummarizationService(db)
        result = await service.summarize_message(
            user_id=current_user.id,
            message_id=request.message_id
        )

        return SummaryResponse(**result)

    except NotFoundError as e:
        logger.error(f"Message not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except SummarizationError as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in message summarization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Summarization service error"
        )


@router.post(
    "/document",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK
)
async def summarize_document(
    request: DocumentSummarizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Summarize document content.

    - **content**: Document text content (minimum 100 characters)
    - **content_type**: Type of content (text, pdf, docx)

    Returns summary with extracted keywords and processing time.
    """
    try:
        service = SummarizationService(db)
        result = await service.summarize_document(
            user_id=current_user.id,
            content=request.content,
            content_type=request.content_type
        )

        return SummaryResponse(**result)

    except SummarizationError as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in document summarization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Summarization service error"
        )


@router.get(
    "/keywords/{summary_id}",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse}
    }
)
async def get_keywords(
    summary_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Get keywords for a specific summary.

    - **summary_id**: Summary ID

    Returns list of extracted keywords.
    """
    try:
        service = SummarizationService(db)
        keywords = service.get_keywords(summary_id)

        return keywords

    except NotFoundError as e:
        logger.error(f"Summary not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error retrieving keywords: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve keywords"
        )


@router.get(
    "/history",
    response_model=List[SummaryResponse],
    status_code=status.HTTP_200_OK
)
async def get_summary_history(
    content_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Get summarization history for current user.

    - **content_type**: Optional filter by content type (chat, message, document)
    - **limit**: Maximum number of results (default: 50)
    - **offset**: Number of results to skip (default: 0)

    Returns list of past summaries.
    """
    try:
        service = SummarizationService(db)
        summaries = service.get_user_summaries(
            user_id=current_user.id,
            content_type=content_type,
            limit=limit,
            offset=offset
        )

        return [SummaryResponse(**s) for s in summaries]

    except Exception as e:
        logger.error(f"Error retrieving summary history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve summary history"
        )

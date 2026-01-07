"""
Translation API routes.

This module provides REST API endpoints for translation operations.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import structlog

from src.api.dependencies import get_db, get_current_user_optional
from src.models.schemas import (
    TranslationRequest,
    TranslationBatchRequest,
    TranslationResponse,
    ErrorResponse
)
from src.models.database import User
from src.services.translation_service import TranslationService
from src.core.exceptions import TranslationError

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/translate", tags=["translation"])


@router.post(
    "",
    response_model=TranslationResponse,
    status_code=status.HTTP_200_OK,
    responses={
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def translate_text(
    request: TranslationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Translate text to target language.

    - **text**: Text to translate (1-10,000 characters)
    - **target_lang**: Target language code (ko, en, ja, zh)
    - **source_lang**: Source language code (optional, auto-detected if not provided)

    Returns translation result with cache status.
    """
    try:
        service = TranslationService(db)
        result = await service.translate(
            user_id=current_user.id,
            text=request.text,
            target_lang=request.target_lang,
            source_lang=request.source_lang
        )

        return TranslationResponse(**result)

    except TranslationError as e:
        logger.error(f"Translation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in translation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Translation service error"
        )


@router.post(
    "/batch",
    response_model=List[TranslationResponse],
    status_code=status.HTTP_200_OK
)
async def translate_batch(
    request: TranslationBatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Translate multiple texts in batch.

    - **texts**: List of texts to translate (1-10 texts)
    - **target_lang**: Target language code (ko, en, ja, zh)
    - **source_lang**: Source language code (optional)

    Returns list of translation results.
    """
    try:
        service = TranslationService(db)
        results = await service.translate_batch(
            user_id=current_user.id,
            texts=request.texts,
            target_lang=request.target_lang,
            source_lang=request.source_lang
        )

        return [
            TranslationResponse(**r) if "error" not in r else None
            for r in results
        ]

    except TranslationError as e:
        logger.error(f"Batch translation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in batch translation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch translation service error"
        )


@router.get(
    "/history",
    response_model=List[TranslationResponse],
    status_code=status.HTTP_200_OK
)
async def get_translation_history(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Get translation history for current user.

    - **limit**: Maximum number of results (default: 50)
    - **offset**: Number of results to skip (default: 0)

    Returns list of past translations.
    """
    try:
        service = TranslationService(db)
        history = service.get_history(
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )

        return [TranslationResponse(**h) for h in history]

    except Exception as e:
        logger.error(f"Error retrieving translation history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve translation history"
        )


@router.get(
    "/stats/cache",
    status_code=status.HTTP_200_OK
)
async def get_cache_stats(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Get cache statistics for current user.

    - **days**: Number of days to look back (default: 7)

    Returns cache hit rate and related statistics.
    """
    try:
        service = TranslationService(db)
        stats = service.get_cache_stats(
            user_id=current_user.id,
            days=days
        )

        return stats

    except Exception as e:
        logger.error(f"Error retrieving cache stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cache statistics"
        )

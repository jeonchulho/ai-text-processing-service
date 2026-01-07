"""
Schedule API routes.

This module provides REST API endpoints for schedule detection and management.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import structlog

from src.api.dependencies import get_db, get_current_user_optional
from src.models.schemas import (
    ScheduleDetectionRequest,
    ScheduleDetectionResponse,
    ScheduleConfirmRequest,
    ScheduleResponse,
    ScheduleConflictResponse,
    ErrorResponse
)
from src.models.database import User
from src.services.schedule_service import ScheduleService
from src.core.exceptions import ScheduleDetectionError, NotFoundError

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/schedule", tags=["schedule"])


@router.post(
    "/detect",
    response_model=ScheduleDetectionResponse,
    status_code=status.HTTP_200_OK,
    responses={
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def detect_schedule(
    request: ScheduleDetectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Detect schedule information from text.

    - **text**: Text to analyze for schedule information (1-2000 characters)

    Returns detection result with extracted entities and potential conflicts.
    """
    try:
        service = ScheduleService(db)
        result = await service.detect_schedule(
            user_id=current_user.id,
            text=request.text
        )

        return ScheduleDetectionResponse(**result)

    except ScheduleDetectionError as e:
        logger.error(f"Schedule detection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in schedule detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Schedule detection service error"
        )


@router.post(
    "/confirm",
    response_model=ScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        422: {"model": ErrorResponse}
    }
)
async def confirm_schedule(
    request: ScheduleConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Confirm and create a schedule.

    - **title**: Schedule title
    - **start_time**: Start datetime
    - **end_time**: End datetime (optional)
    - **location**: Location (optional)
    - **attendees**: List of attendee names/emails (optional)
    - **source_text**: Original detection text (optional)

    Returns created schedule with conflict information.
    """
    try:
        service = ScheduleService(db)
        result = await service.confirm_schedule(
            user_id=current_user.id,
            title=request.title,
            start_time=request.start_time,
            end_time=request.end_time,
            location=request.location,
            attendees=request.attendees,
            source_text=request.source_text
        )

        return ScheduleResponse(**result)

    except ScheduleDetectionError as e:
        logger.error(f"Schedule confirmation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in schedule confirmation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Schedule confirmation service error"
        )


@router.get(
    "/conflicts",
    response_model=ScheduleConflictResponse,
    status_code=status.HTTP_200_OK
)
async def check_conflicts(
    start_time: datetime,
    end_time: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Check for schedule conflicts.

    - **start_time**: Start datetime to check
    - **end_time**: End datetime to check (optional, defaults to 1 hour after start)

    Returns list of conflicting schedules.
    """
    try:
        service = ScheduleService(db)
        result = service.check_conflicts(
            user_id=current_user.id,
            start_time=start_time,
            end_time=end_time
        )

        # Convert to proper response format
        response = ScheduleConflictResponse(
            has_conflict=result["has_conflict"],
            conflicting_schedules=[
                ScheduleResponse(
                    id=s["id"],
                    title=s["title"],
                    start_time=s["start_time"],
                    end_time=s.get("end_time"),
                    location=s.get("location"),
                    attendees=s.get("attendees", []),
                    is_confirmed=True,
                    created_at=datetime.utcnow()  # Placeholder
                )
                for s in result["conflicting_schedules"]
            ]
        )

        return response

    except Exception as e:
        logger.error(f"Error checking conflicts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check conflicts"
        )


@router.get(
    "/{schedule_id}",
    response_model=ScheduleResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse}
    }
)
async def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Get schedule by ID.

    - **schedule_id**: Schedule ID

    Returns schedule details.
    """
    try:
        service = ScheduleService(db)
        result = service.get_schedule(schedule_id)

        return ScheduleResponse(**result)

    except NotFoundError as e:
        logger.error(f"Schedule not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error retrieving schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve schedule"
        )


@router.delete(
    "/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse}
    }
)
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Delete a schedule.

    - **schedule_id**: Schedule ID to delete

    Returns 204 No Content on success.
    """
    try:
        service = ScheduleService(db)
        service.delete_schedule(schedule_id)

        return None

    except NotFoundError as e:
        logger.error(f"Schedule not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete schedule"
        )


@router.get(
    "",
    response_model=List[ScheduleResponse],
    status_code=status.HTTP_200_OK
)
async def list_schedules(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Get user's schedules.

    - **start_date**: Filter by start date (optional)
    - **end_date**: Filter by end date (optional)
    - **limit**: Maximum number of results (default: 100)
    - **offset**: Number of results to skip (default: 0)

    Returns list of schedules.
    """
    try:
        service = ScheduleService(db)
        schedules = service.get_user_schedules(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )

        return [ScheduleResponse(**s, created_at=datetime.utcnow()) for s in schedules]

    except Exception as e:
        logger.error(f"Error retrieving schedules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve schedules"
        )


@router.get(
    "/upcoming",
    response_model=List[ScheduleResponse],
    status_code=status.HTTP_200_OK
)
async def get_upcoming_schedules(
    hours: int = 24,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Get upcoming confirmed schedules.

    - **hours**: Hours to look ahead (default: 24)
    - **limit**: Maximum number of results (default: 10)

    Returns list of upcoming schedules.
    """
    try:
        service = ScheduleService(db)
        schedules = service.get_upcoming_schedules(
            user_id=current_user.id,
            hours=hours,
            limit=limit
        )

        return [ScheduleResponse(**s, is_confirmed=True, created_at=datetime.utcnow()) for s in schedules]

    except Exception as e:
        logger.error(f"Error retrieving upcoming schedules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve upcoming schedules"
        )

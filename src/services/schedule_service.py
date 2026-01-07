"""
Schedule service.

This service provides high-level schedule operations,
integrating the workflow with database persistence.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
import structlog

from src.workflows.schedule_workflow import schedule_workflow, ScheduleState
from src.repositories.schedule_repository import ScheduleRepository
from src.core.exceptions import ScheduleDetectionError, NotFoundError
from src.core.config import settings

logger = structlog.get_logger(__name__)


class ScheduleService:
    """Service for schedule operations."""

    def __init__(self, db: Session):
        """
        Initialize service with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.repository = ScheduleRepository(db)

    async def detect_schedule(
        self,
        user_id: int,
        text: str
    ) -> dict:
        """
        Detect schedule from text.

        Args:
            user_id: User ID
            text: Text to analyze

        Returns:
            Dictionary with detection result
        """
        try:
            # Validate feature is enabled
            if not settings.ENABLE_SCHEDULE_DETECTION:
                raise ScheduleDetectionError("Schedule detection feature is disabled")

            # Run workflow
            initial_state: ScheduleState = {
                "message": text,
                "user_id": user_id,
                "detected": False,
                "entities": None,
                "conflicts": [],
                "approved": False,
                "error": None
            }

            result = schedule_workflow.invoke(initial_state)

            # Check for errors
            if result.get("error"):
                raise ScheduleDetectionError(result["error"])

            response = {
                "detected": result["detected"],
                "source_text": text
            }

            if result["detected"] and result.get("entities"):
                entities = result["entities"]
                response["entities"] = {
                    "title": entities.get("title", ""),
                    "start_time": entities.get("start_time"),
                    "end_time": entities.get("end_time"),
                    "location": entities.get("location"),
                    "attendees": entities.get("attendees", []),
                    "confidence_score": entities.get("confidence_score", 0.0)
                }

                if result.get("conflicts"):
                    response["conflicts"] = result["conflicts"]

            logger.info(f"Schedule detection completed: detected={result['detected']}")
            return response

        except ScheduleDetectionError:
            raise
        except Exception as e:
            logger.error(f"Schedule detection error: {e}")
            raise ScheduleDetectionError(f"Schedule detection failed: {e}")

    async def confirm_schedule(
        self,
        user_id: int,
        title: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        source_text: Optional[str] = None,
        confidence_score: Optional[float] = None
    ) -> dict:
        """
        Confirm and create a schedule.

        Args:
            user_id: User ID
            title: Schedule title
            start_time: Start datetime
            end_time: End datetime (optional)
            location: Location (optional)
            attendees: List of attendee names/emails
            source_text: Original detection text
            confidence_score: Detection confidence

        Returns:
            Dictionary with created schedule
        """
        try:
            # Check for conflicts
            conflicts = self.repository.check_conflicts(
                user_id=user_id,
                start_time=start_time,
                end_time=end_time
            )

            if conflicts:
                logger.warning(f"Schedule has {len(conflicts)} conflicts")

            # Create schedule
            schedule = self.repository.create(
                user_id=user_id,
                title=title,
                start_time=start_time,
                end_time=end_time,
                location=location,
                attendees=attendees or [],
                source_text=source_text,
                confidence_score=confidence_score,
                is_confirmed=True
            )

            logger.info(f"Schedule created: {schedule.id}")

            return {
                "id": schedule.id,
                "title": schedule.title,
                "start_time": schedule.start_time,
                "end_time": schedule.end_time,
                "location": schedule.location,
                "attendees": schedule.attendees,
                "is_confirmed": schedule.is_confirmed,
                "conflicts": [
                    {
                        "id": c.id,
                        "title": c.title,
                        "start_time": c.start_time
                    }
                    for c in conflicts
                ],
                "created_at": schedule.created_at
            }

        except Exception as e:
            logger.error(f"Schedule confirmation error: {e}")
            raise ScheduleDetectionError(f"Schedule confirmation failed: {e}")

    def get_schedule(self, schedule_id: int) -> dict:
        """
        Get schedule by ID.

        Args:
            schedule_id: Schedule ID

        Returns:
            Dictionary with schedule details
        """
        try:
            schedule = self.repository.get_by_id(schedule_id)

            if not schedule:
                raise NotFoundError(f"Schedule {schedule_id} not found")

            return {
                "id": schedule.id,
                "title": schedule.title,
                "start_time": schedule.start_time,
                "end_time": schedule.end_time,
                "location": schedule.location,
                "attendees": schedule.attendees,
                "is_confirmed": schedule.is_confirmed,
                "created_at": schedule.created_at
            }

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Schedule retrieval error: {e}")
            raise ScheduleDetectionError(f"Failed to retrieve schedule: {e}")

    def get_user_schedules(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[dict]:
        """
        Get user's schedules.

        Args:
            user_id: User ID
            start_date: Filter by start date (optional)
            end_date: Filter by end date (optional)
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of schedule records
        """
        try:
            schedules = self.repository.get_user_schedules(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                offset=offset
            )

            return [
                {
                    "id": s.id,
                    "title": s.title,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "location": s.location,
                    "attendees": s.attendees,
                    "is_confirmed": s.is_confirmed
                }
                for s in schedules
            ]

        except Exception as e:
            logger.error(f"Schedules retrieval error: {e}")
            raise ScheduleDetectionError(f"Failed to retrieve schedules: {e}")

    def check_conflicts(
        self,
        user_id: int,
        start_time: datetime,
        end_time: Optional[datetime] = None
    ) -> dict:
        """
        Check for schedule conflicts.

        Args:
            user_id: User ID
            start_time: Start time to check
            end_time: End time to check (optional)

        Returns:
            Dictionary with conflict information
        """
        try:
            conflicts = self.repository.check_conflicts(
                user_id=user_id,
                start_time=start_time,
                end_time=end_time
            )

            return {
                "has_conflict": len(conflicts) > 0,
                "conflicting_schedules": [
                    {
                        "id": s.id,
                        "title": s.title,
                        "start_time": s.start_time,
                        "end_time": s.end_time,
                        "location": s.location
                    }
                    for s in conflicts
                ]
            }

        except Exception as e:
            logger.error(f"Conflict check error: {e}")
            raise ScheduleDetectionError(f"Conflict check failed: {e}")

    def delete_schedule(self, schedule_id: int) -> bool:
        """
        Delete a schedule.

        Args:
            schedule_id: Schedule ID to delete

        Returns:
            True if deleted successfully
        """
        try:
            return self.repository.delete(schedule_id)

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Schedule deletion error: {e}")
            raise ScheduleDetectionError(f"Schedule deletion failed: {e}")

    def get_upcoming_schedules(
        self,
        user_id: int,
        hours: int = 24,
        limit: int = 10
    ) -> List[dict]:
        """
        Get upcoming confirmed schedules.

        Args:
            user_id: User ID
            hours: Hours to look ahead
            limit: Maximum number of results

        Returns:
            List of upcoming schedules
        """
        try:
            schedules = self.repository.get_upcoming_schedules(
                user_id=user_id,
                hours=hours,
                limit=limit
            )

            return [
                {
                    "id": s.id,
                    "title": s.title,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "location": s.location,
                    "attendees": s.attendees
                }
                for s in schedules
            ]

        except Exception as e:
            logger.error(f"Upcoming schedules retrieval error: {e}")
            raise ScheduleDetectionError(f"Failed to retrieve upcoming schedules: {e}")

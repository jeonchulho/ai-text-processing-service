"""
Schedule repository for database operations.

This module handles all database operations related to schedules,
including CRUD operations and conflict detection.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
import structlog

from src.models.database import Schedule
from src.core.exceptions import DatabaseError, NotFoundError

logger = structlog.get_logger(__name__)


class ScheduleRepository:
    """Repository for schedule database operations."""

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
        title: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        description: Optional[str] = None,
        source_text: Optional[str] = None,
        confidence_score: Optional[float] = None,
        is_confirmed: bool = False,
        external_id: Optional[str] = None
    ) -> Schedule:
        """
        Create a new schedule record.

        Args:
            user_id: User ID
            title: Schedule title
            start_time: Start datetime
            end_time: End datetime (optional)
            location: Location (optional)
            attendees: List of attendee names/emails
            description: Description (optional)
            source_text: Original detection text
            confidence_score: Detection confidence (0-1)
            is_confirmed: Whether schedule is confirmed
            external_id: External calendar event ID

        Returns:
            Created Schedule object
        """
        try:
            schedule = Schedule(
                user_id=user_id,
                title=title,
                start_time=start_time,
                end_time=end_time,
                location=location,
                attendees=attendees or [],
                description=description,
                source_text=source_text,
                confidence_score=confidence_score,
                is_confirmed=is_confirmed,
                external_id=external_id
            )

            self.db.add(schedule)
            self.db.commit()
            self.db.refresh(schedule)

            logger.info(f"Created schedule record: {schedule.id}")
            return schedule

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create schedule: {e}")
            raise DatabaseError(f"Schedule creation failed: {e}")

    def get_by_id(self, schedule_id: int) -> Optional[Schedule]:
        """
        Get schedule by ID.

        Args:
            schedule_id: Schedule ID

        Returns:
            Schedule object or None
        """
        try:
            return self.db.query(Schedule).filter(
                Schedule.id == schedule_id
            ).first()
        except Exception as e:
            logger.error(f"Failed to get schedule {schedule_id}: {e}")
            raise DatabaseError(f"Schedule retrieval failed: {e}")

    def get_user_schedules(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Schedule]:
        """
        Get user's schedules.

        Args:
            user_id: User ID
            start_date: Filter by start date (optional)
            end_date: Filter by end date (optional)
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of Schedule objects
        """
        try:
            query = self.db.query(Schedule).filter(
                Schedule.user_id == user_id
            )

            if start_date:
                query = query.filter(Schedule.start_time >= start_date)

            if end_date:
                query = query.filter(Schedule.start_time <= end_date)

            return query.order_by(
                Schedule.start_time
            ).limit(limit).offset(offset).all()

        except Exception as e:
            logger.error(f"Failed to get user schedules: {e}")
            raise DatabaseError(f"Schedules retrieval failed: {e}")

    def check_conflicts(
        self,
        user_id: int,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        exclude_id: Optional[int] = None
    ) -> List[Schedule]:
        """
        Check for schedule conflicts.

        Args:
            user_id: User ID
            start_time: Start time to check
            end_time: End time to check (optional)
            exclude_id: Schedule ID to exclude from check

        Returns:
            List of conflicting schedules
        """
        try:
            # If no end_time, assume 1 hour duration
            if not end_time:
                end_time = start_time + timedelta(hours=1)

            # Find overlapping schedules
            query = self.db.query(Schedule).filter(
                Schedule.user_id == user_id,
                Schedule.is_confirmed == True
            )

            if exclude_id:
                query = query.filter(Schedule.id != exclude_id)

            # Check for overlap:
            # A schedule overlaps if:
            # - It starts before this event ends AND
            # - It ends after this event starts (or has no end time)
            conflicts = query.filter(
                Schedule.start_time < end_time,
                or_(
                    Schedule.end_time.is_(None),
                    Schedule.end_time > start_time
                )
            ).all()

            logger.info(f"Found {len(conflicts)} conflicting schedules")
            return conflicts

        except Exception as e:
            logger.error(f"Failed to check conflicts: {e}")
            raise DatabaseError(f"Conflict check failed: {e}")

    def update(
        self,
        schedule_id: int,
        **kwargs
    ) -> Schedule:
        """
        Update a schedule.

        Args:
            schedule_id: Schedule ID to update
            **kwargs: Fields to update

        Returns:
            Updated Schedule object
        """
        try:
            schedule = self.get_by_id(schedule_id)
            if not schedule:
                raise NotFoundError(f"Schedule {schedule_id} not found")

            for key, value in kwargs.items():
                if hasattr(schedule, key):
                    setattr(schedule, key, value)

            schedule.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(schedule)

            logger.info(f"Updated schedule: {schedule_id}")
            return schedule

        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update schedule: {e}")
            raise DatabaseError(f"Schedule update failed: {e}")

    def confirm_schedule(self, schedule_id: int) -> Schedule:
        """
        Confirm a schedule.

        Args:
            schedule_id: Schedule ID to confirm

        Returns:
            Updated Schedule object
        """
        return self.update(schedule_id, is_confirmed=True)

    def delete(self, schedule_id: int) -> bool:
        """
        Delete a schedule record.

        Args:
            schedule_id: Schedule ID to delete

        Returns:
            True if deleted successfully
        """
        try:
            schedule = self.get_by_id(schedule_id)
            if not schedule:
                raise NotFoundError(f"Schedule {schedule_id} not found")

            self.db.delete(schedule)
            self.db.commit()

            logger.info(f"Deleted schedule: {schedule_id}")
            return True

        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete schedule: {e}")
            raise DatabaseError(f"Schedule deletion failed: {e}")

    def get_upcoming_schedules(
        self,
        user_id: int,
        hours: int = 24,
        limit: int = 10
    ) -> List[Schedule]:
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
            now = datetime.utcnow()
            until = now + timedelta(hours=hours)

            return self.db.query(Schedule).filter(
                Schedule.user_id == user_id,
                Schedule.is_confirmed == True,
                Schedule.start_time >= now,
                Schedule.start_time <= until
            ).order_by(
                Schedule.start_time
            ).limit(limit).all()

        except Exception as e:
            logger.error(f"Failed to get upcoming schedules: {e}")
            raise DatabaseError(f"Upcoming schedules retrieval failed: {e}")

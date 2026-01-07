"""
Schedule detection workflow using LangGraph.

This workflow orchestrates schedule detection including:
- Pattern detection
- Entity extraction (NER)
- Conflict checking
- User approval
"""

from typing import TypedDict, Optional, Dict, Any, List, Literal
from datetime import datetime
from langgraph.graph import StateGraph, END
import structlog

from src.utils.llm_client import llm_client
from src.core.exceptions import ScheduleDetectionError

logger = structlog.get_logger(__name__)


class ScheduleState(TypedDict):
    """State for schedule detection workflow."""
    message: str
    user_id: int
    detected: bool
    entities: Optional[Dict[str, Any]]
    conflicts: List[Dict[str, Any]]
    approved: bool
    error: Optional[str]


def detect_schedule_pattern(state: ScheduleState) -> ScheduleState:
    """
    Detect if message contains schedule information.

    Args:
        state: Current workflow state

    Returns:
        Updated state
    """
    try:
        # Use LLM to detect schedule
        result = llm_client.detect_schedule(state["message"])

        if result.get("has_schedule"):
            state["detected"] = True
            state["entities"] = result
            logger.info("Schedule detected in message")
        else:
            state["detected"] = False
            logger.info("No schedule detected in message")

    except Exception as e:
        logger.error(f"Schedule detection error: {e}")
        state["error"] = str(e)
        state["detected"] = False

    return state


def extract_entities(state: ScheduleState) -> ScheduleState:
    """
    Extract and validate schedule entities.

    Args:
        state: Current workflow state

    Returns:
        Updated state
    """
    try:
        if not state.get("entities"):
            return state

        entities = state["entities"]

        # Parse and validate date/time
        if entities.get("date") and entities.get("time"):
            try:
                date_str = entities["date"]
                time_str = entities["time"]

                # Combine date and time
                datetime_str = f"{date_str} {time_str}"
                start_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")

                entities["start_time"] = start_time
                entities["confidence_score"] = 0.8  # Base confidence

                # Increase confidence if more details present
                if entities.get("location"):
                    entities["confidence_score"] += 0.1
                if entities.get("attendees"):
                    entities["confidence_score"] += 0.1

                logger.info(f"Parsed schedule: {entities['title']} at {start_time}")

            except ValueError as e:
                logger.error(f"Date/time parsing error: {e}")
                state["error"] = "Invalid date/time format"
                state["detected"] = False

        else:
            logger.warning("Missing date or time in detected schedule")
            state["detected"] = False

    except Exception as e:
        logger.error(f"Entity extraction error: {e}")
        state["error"] = str(e)

    return state


def check_conflicts(state: ScheduleState) -> ScheduleState:
    """
    Check for schedule conflicts.

    Args:
        state: Current workflow state

    Returns:
        Updated state
    """
    try:
        if not state.get("entities") or not state["entities"].get("start_time"):
            return state

        # Import here to avoid circular dependency
        from src.repositories.schedule_repository import ScheduleRepository
        from sqlalchemy.orm import Session
        from src.models.database import Base
        from sqlalchemy import create_engine
        from src.core.config import settings

        # Create database session
        engine = create_engine(settings.DATABASE_URL)
        db = Session(engine)

        try:
            repo = ScheduleRepository(db)
            start_time = state["entities"]["start_time"]

            # Check for conflicts
            conflicts = repo.check_conflicts(
                user_id=state["user_id"],
                start_time=start_time
            )

            state["conflicts"] = [
                {
                    "id": s.id,
                    "title": s.title,
                    "start_time": s.start_time.isoformat(),
                    "end_time": s.end_time.isoformat() if s.end_time else None
                }
                for s in conflicts
            ]

            if conflicts:
                logger.warning(f"Found {len(conflicts)} conflicting schedules")
            else:
                logger.info("No schedule conflicts found")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Conflict check error: {e}")
        # Don't fail workflow, just log the error
        state["conflicts"] = []

    return state


def should_extract_entities(state: ScheduleState) -> Literal["extract", "end"]:
    """
    Determine if entity extraction is needed.

    Args:
        state: Current workflow state

    Returns:
        Next node to execute
    """
    if state["detected"]:
        return "extract"
    return "end"


def should_check_conflicts(state: ScheduleState) -> Literal["conflicts", "end"]:
    """
    Determine if conflict checking is needed.

    Args:
        state: Current workflow state

    Returns:
        Next node to execute
    """
    if state["detected"] and state.get("entities") and not state.get("error"):
        return "conflicts"
    return "end"


def create_schedule_workflow() -> StateGraph:
    """
    Create the schedule detection workflow graph.

    Returns:
        Configured StateGraph
    """
    workflow = StateGraph(ScheduleState)

    # Add nodes
    workflow.add_node("detect", detect_schedule_pattern)
    workflow.add_node("extract", extract_entities)
    workflow.add_node("conflicts", check_conflicts)

    # Define edges
    workflow.set_entry_point("detect")
    workflow.add_conditional_edges(
        "detect",
        should_extract_entities,
        {
            "extract": "extract",
            "end": END
        }
    )
    workflow.add_conditional_edges(
        "extract",
        should_check_conflicts,
        {
            "conflicts": "conflicts",
            "end": END
        }
    )
    workflow.add_edge("conflicts", END)

    return workflow.compile()


# Create global workflow instance
schedule_workflow = create_schedule_workflow()

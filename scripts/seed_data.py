"""
Seed data script.

This script populates the database with sample data for testing.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import structlog

from src.core.config import settings
from src.models.database import User, ChatMessage, DirectMessage
from src.core.security import get_password_hash

logger = structlog.get_logger(__name__)


def seed_data():
    """Seed database with sample data."""
    try:
        logger.info("Seeding database with sample data...")
        
        # Create engine and session
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Get test user
            test_user = db.query(User).filter(User.username == "test_user").first()
            
            if not test_user:
                logger.error("Test user not found. Please run init_db.py first.")
                return False
            
            # Check if data already exists
            existing_messages = db.query(ChatMessage).count()
            
            if existing_messages > 0:
                logger.info("Sample data already exists")
                return True
            
            # Create sample chat messages
            chat_messages = [
                ChatMessage(
                    chat_id="test_chat_1",
                    user_id=test_user.id,
                    sender_name="Alice",
                    message="Hi everyone! How's the project going?",
                    timestamp=datetime.utcnow() - timedelta(hours=2)
                ),
                ChatMessage(
                    chat_id="test_chat_1",
                    user_id=test_user.id,
                    sender_name="Bob",
                    message="Great! I've finished the initial design.",
                    timestamp=datetime.utcnow() - timedelta(hours=2, minutes=-5)
                ),
                ChatMessage(
                    chat_id="test_chat_1",
                    user_id=test_user.id,
                    sender_name="Charlie",
                    message="Nice work! I'll start on the implementation tomorrow.",
                    timestamp=datetime.utcnow() - timedelta(hours=2, minutes=-10)
                ),
                ChatMessage(
                    chat_id="test_chat_1",
                    user_id=test_user.id,
                    sender_name="Alice",
                    message="Let's have a meeting on Friday at 2 PM to discuss progress.",
                    timestamp=datetime.utcnow() - timedelta(hours=2, minutes=-15)
                ),
                ChatMessage(
                    chat_id="test_chat_1",
                    user_id=test_user.id,
                    sender_name="Bob",
                    message="Sounds good! I'll prepare the slides.",
                    timestamp=datetime.utcnow() - timedelta(hours=2, minutes=-20)
                ),
            ]
            
            for msg in chat_messages:
                db.add(msg)
            
            # Create sample direct messages
            direct_messages = [
                DirectMessage(
                    sender_id=test_user.id,
                    receiver_id=test_user.id,
                    subject="Important Update",
                    message="Hi, I wanted to share some important updates about the project. We've made significant progress on the core features and are on track to meet our deadlines. Please review the attached documents and let me know if you have any questions.",
                    is_read=False
                ),
                DirectMessage(
                    sender_id=test_user.id,
                    receiver_id=test_user.id,
                    subject="Meeting Reminder",
                    message="Just a quick reminder about our meeting tomorrow at 10 AM in Conference Room B. We'll be discussing the Q1 roadmap and resource allocation.",
                    is_read=True
                ),
            ]
            
            for msg in direct_messages:
                db.add(msg)
            
            db.commit()
            
            logger.info(f"Created {len(chat_messages)} chat messages")
            logger.info(f"Created {len(direct_messages)} direct messages")
            logger.info("Sample data seeded successfully")
            
            return True
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Data seeding failed: {e}")
        return False


if __name__ == "__main__":
    success = seed_data()
    sys.exit(0 if success else 1)

"""
Database initialization script.

This script creates all database tables and optionally seeds initial data.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import structlog

from src.core.config import settings
from src.models.database import Base, User
from src.core.security import get_password_hash

logger = structlog.get_logger(__name__)


def init_database():
    """Initialize database tables."""
    try:
        logger.info("Initializing database...")
        logger.info(f"Database URL: {settings.DATABASE_URL}")
        
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database tables created successfully")
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Check if test user exists
            test_user = db.query(User).filter(User.username == "test_user").first()
            
            if not test_user:
                # Create test user
                test_user = User(
                    username="test_user",
                    email="test@example.com",
                    hashed_password=get_password_hash("test_password"),
                    full_name="Test User",
                    is_active=True,
                    is_superuser=False
                )
                db.add(test_user)
                db.commit()
                logger.info("Created test user (username: test_user, password: test_password)")
            else:
                logger.info("Test user already exists")
            
            # Check if admin user exists
            admin_user = db.query(User).filter(User.username == "admin").first()
            
            if not admin_user:
                # Create admin user
                admin_user = User(
                    username="admin",
                    email="admin@example.com",
                    hashed_password=get_password_hash("admin_password"),
                    full_name="Admin User",
                    is_active=True,
                    is_superuser=True
                )
                db.add(admin_user)
                db.commit()
                logger.info("Created admin user (username: admin, password: admin_password)")
            else:
                logger.info("Admin user already exists")
                
        finally:
            db.close()
        
        logger.info("Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)

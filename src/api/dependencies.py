"""
Dependency injection for FastAPI routes.

This module provides dependencies for database sessions,
authentication, and other shared resources.
"""

from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import structlog

from src.core.config import settings
from src.core.security import decode_access_token
from src.core.exceptions import AuthenticationError
from src.models.database import Base, User

logger = structlog.get_logger(__name__)

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Security scheme
security = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user.

    Args:
        credentials: HTTP authorization credentials
        db: Database session

    Returns:
        Current user

    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user if authenticated, otherwise return mock user.
    
    This is for development/testing purposes.

    Args:
        credentials: HTTP authorization credentials
        db: Database session

    Returns:
        Current user or mock user
    """
    try:
        if credentials:
            return get_current_user(credentials, db)
    except HTTPException:
        pass

    # Return mock user for testing (user_id = 1)
    # In production, this should require authentication
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        # Create mock user if doesn't exist
        user = User(
            id=1,
            username="test_user",
            email="test@example.com",
            hashed_password="mock",
            full_name="Test User",
            is_active=True
        )
        db.add(user)
        db.commit()

    return user


def create_tables():
    """Create all database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

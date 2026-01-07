"""
Database models using SQLAlchemy ORM.

This module defines all database tables and relationships
for the AI Text Processing Service.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean,
    ForeignKey, Float, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    translations = relationship("Translation", back_populates="user")
    summaries = relationship("Summary", back_populates="user")
    schedules = relationship("Schedule", back_populates="user")


class Translation(Base):
    """Translation history model."""

    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=False)
    source_lang = Column(String(10), nullable=False)
    target_lang = Column(String(10), nullable=False)
    cache_hit = Column(Boolean, default=False)
    vector_stored = Column(Boolean, default=False)
    model_used = Column(String(50))
    token_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="translations")


class Summary(Base):
    """Summary results model."""

    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_type = Column(String(50), nullable=False)  # chat, message, document
    original_content = Column(Text, nullable=False)
    summary_text = Column(Text, nullable=False)
    keywords = Column(JSON)  # List of extracted keywords
    chunk_count = Column(Integer)
    model_used = Column(String(50))
    token_count = Column(Integer)
    processing_time = Column(Float)  # seconds
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="summaries")


class Schedule(Base):
    """Schedule/calendar event model."""

    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    location = Column(String(200))
    attendees = Column(JSON)  # List of attendee emails/names
    source_text = Column(Text)  # Original message that triggered detection
    confidence_score = Column(Float)  # Detection confidence
    is_confirmed = Column(Boolean, default=False)
    external_id = Column(String(100))  # Google Calendar or Outlook event ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="schedules")


class ChatMessage(Base):
    """Chat message model for testing and summarization."""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String(100), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    sender_name = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    message_type = Column(String(20), default="text")  # text, image, file, etc.


class DirectMessage(Base):
    """Direct message (쪽지) model for testing and summarization."""

    __tablename__ = "direct_messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(200))
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

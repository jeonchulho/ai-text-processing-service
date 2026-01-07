"""
Pydantic schemas for request/response validation.

This module defines all Pydantic models used for API
request validation and response serialization.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


# User Schemas
class UserBase(BaseModel):
    """Base user schema."""
    username: str
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for user creation."""
    password: str


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Translation Schemas
class TranslationRequest(BaseModel):
    """Schema for translation request."""
    text: str = Field(..., min_length=1, max_length=10000)
    target_lang: str = Field(..., pattern="^(ko|en|ja|zh)$")
    source_lang: Optional[str] = Field(None, pattern="^(ko|en|ja|zh)$")


class TranslationBatchRequest(BaseModel):
    """Schema for batch translation request."""
    texts: List[str] = Field(..., min_items=1, max_items=10)
    target_lang: str = Field(..., pattern="^(ko|en|ja|zh)$")
    source_lang: Optional[str] = Field(None, pattern="^(ko|en|ja|zh)$")


class TranslationResponse(BaseModel):
    """Schema for translation response."""
    id: int
    source_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    cache_hit: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Summarization Schemas
class ChatSummarizationRequest(BaseModel):
    """Schema for chat summarization request."""
    chat_id: str = Field(..., min_length=1)
    limit: Optional[int] = Field(100, ge=10, le=1000)


class MessageSummarizationRequest(BaseModel):
    """Schema for message summarization request."""
    message_id: int


class DocumentSummarizationRequest(BaseModel):
    """Schema for document summarization request."""
    content: str = Field(..., min_length=100)
    content_type: str = Field(..., pattern="^(text|pdf|docx)$")


class SummaryResponse(BaseModel):
    """Schema for summary response."""
    id: int
    content_type: str
    summary_text: str
    keywords: List[str]
    chunk_count: Optional[int] = None
    processing_time: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Schedule Schemas
class ScheduleDetectionRequest(BaseModel):
    """Schema for schedule detection request."""
    text: str = Field(..., min_length=1, max_length=2000)


class ScheduleEntity(BaseModel):
    """Schema for extracted schedule entities."""
    title: str
    start_time: datetime
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    attendees: List[str] = Field(default_factory=list)
    confidence_score: float


class ScheduleDetectionResponse(BaseModel):
    """Schema for schedule detection response."""
    detected: bool
    entities: Optional[ScheduleEntity] = None
    source_text: str


class ScheduleConfirmRequest(BaseModel):
    """Schema for schedule confirmation request."""
    title: str
    start_time: datetime
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    attendees: List[str] = Field(default_factory=list)
    source_text: str


class ScheduleResponse(BaseModel):
    """Schema for schedule response."""
    id: int
    title: str
    start_time: datetime
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    attendees: List[str]
    is_confirmed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ScheduleConflictResponse(BaseModel):
    """Schema for schedule conflict response."""
    has_conflict: bool
    conflicting_schedules: List[ScheduleResponse]


# Health Check Schema
class HealthCheckResponse(BaseModel):
    """Schema for health check response."""
    status: str
    timestamp: datetime
    services: dict


# Error Response Schema
class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str
    message: str
    details: Optional[dict] = None

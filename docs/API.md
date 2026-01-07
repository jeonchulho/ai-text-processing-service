# API Documentation

## Overview

The AI Text Processing Service provides a RESTful API for translation, summarization, and schedule detection powered by LangGraph and LLMs.

**Base URL**: `http://localhost:8000`  
**API Version**: `/api/v1`

## Authentication

For development, authentication is optional. In production, all endpoints require JWT Bearer tokens.

```
Authorization: Bearer <your_jwt_token>
```

## Rate Limiting

- **Translation**: 100 requests per minute per user
- **Summarization**: 50 requests per minute per user
- **Schedule Detection**: 50 requests per minute per user

## Translation Endpoints

### POST /api/v1/translate

Translate text to target language with automatic caching.

**Request Body:**
```json
{
  "text": "Hello, world!",
  "target_lang": "ko",
  "source_lang": "en"  // optional, auto-detected if not provided
}
```

**Response:**
```json
{
  "id": 1,
  "source_text": "Hello, world!",
  "translated_text": "안녕하세요, 세계!",
  "source_lang": "en",
  "target_lang": "ko",
  "cache_hit": false,
  "created_at": "2024-01-07T12:00:00Z"
}
```

**Supported Languages:**
- `ko`: Korean
- `en`: English
- `ja`: Japanese
- `zh`: Chinese

### POST /api/v1/translate/batch

Translate multiple texts in a single request.

**Request Body:**
```json
{
  "texts": ["Hello", "World", "Test"],
  "target_lang": "ko",
  "source_lang": "en"  // optional
}
```

**Response:**
```json
[
  {
    "id": 1,
    "source_text": "Hello",
    "translated_text": "안녕",
    "source_lang": "en",
    "target_lang": "ko",
    "cache_hit": false,
    "created_at": "2024-01-07T12:00:00Z"
  },
  // ... more results
]
```

### GET /api/v1/translate/history

Get translation history for the current user.

**Query Parameters:**
- `limit` (optional, default: 50): Maximum number of results
- `offset` (optional, default: 0): Number of results to skip

**Response:**
```json
[
  {
    "id": 1,
    "source_text": "Hello",
    "translated_text": "안녕",
    "source_lang": "en",
    "target_lang": "ko",
    "cache_hit": true,
    "created_at": "2024-01-07T12:00:00Z"
  }
]
```

### GET /api/v1/translate/stats/cache

Get cache statistics.

**Query Parameters:**
- `days` (optional, default: 7): Number of days to analyze

**Response:**
```json
{
  "cache_hit_rate": 0.75,
  "days": 7
}
```

## Summarization Endpoints

### POST /api/v1/summarize/chat

Summarize chat conversation.

**Request Body:**
```json
{
  "chat_id": "test_chat_1",
  "limit": 100  // optional, 10-1000
}
```

**Response:**
```json
{
  "id": 1,
  "content_type": "chat",
  "summary_text": "The team discussed project progress...",
  "keywords": ["project", "meeting", "design", "implementation"],
  "chunk_count": 1,
  "processing_time": 2.5,
  "created_at": "2024-01-07T12:00:00Z"
}
```

### POST /api/v1/summarize/message

Summarize direct message.

**Request Body:**
```json
{
  "message_id": 1
}
```

**Response:** Same format as chat summarization.

### POST /api/v1/summarize/document

Summarize document content.

**Request Body:**
```json
{
  "content": "Long document text...",
  "content_type": "text"  // text, pdf, docx
}
```

**Response:**
```json
{
  "id": 1,
  "content_type": "document",
  "summary_text": "The document discusses...",
  "keywords": ["topic1", "topic2", "topic3"],
  "chunk_count": 5,
  "processing_time": 8.2,
  "created_at": "2024-01-07T12:00:00Z"
}
```

### GET /api/v1/summarize/keywords/{summary_id}

Get keywords for a specific summary.

**Response:**
```json
["keyword1", "keyword2", "keyword3"]
```

### GET /api/v1/summarize/history

Get summarization history.

**Query Parameters:**
- `content_type` (optional): Filter by type (chat, message, document)
- `limit` (optional, default: 50): Maximum number of results
- `offset` (optional, default: 0): Number of results to skip

## Schedule Endpoints

### POST /api/v1/schedule/detect

Detect schedule information from natural language text.

**Request Body:**
```json
{
  "text": "Let's meet tomorrow at 3 PM for the project discussion"
}
```

**Response:**
```json
{
  "detected": true,
  "source_text": "Let's meet tomorrow at 3 PM...",
  "entities": {
    "title": "project discussion",
    "start_time": "2024-01-08T15:00:00Z",
    "end_time": null,
    "location": null,
    "attendees": [],
    "confidence_score": 0.8
  },
  "conflicts": []
}
```

### POST /api/v1/schedule/confirm

Confirm and create a schedule.

**Request Body:**
```json
{
  "title": "Project Discussion",
  "start_time": "2024-01-08T15:00:00Z",
  "end_time": "2024-01-08T16:00:00Z",
  "location": "Conference Room A",
  "attendees": ["user1@example.com", "user2@example.com"],
  "source_text": "Original detection text"  // optional
}
```

**Response:**
```json
{
  "id": 1,
  "title": "Project Discussion",
  "start_time": "2024-01-08T15:00:00Z",
  "end_time": "2024-01-08T16:00:00Z",
  "location": "Conference Room A",
  "attendees": ["user1@example.com", "user2@example.com"],
  "is_confirmed": true,
  "conflicts": [],
  "created_at": "2024-01-07T12:00:00Z"
}
```

### GET /api/v1/schedule/conflicts

Check for schedule conflicts.

**Query Parameters:**
- `start_time` (required): Start datetime (ISO 8601 format)
- `end_time` (optional): End datetime

**Response:**
```json
{
  "has_conflict": true,
  "conflicting_schedules": [
    {
      "id": 2,
      "title": "Another Meeting",
      "start_time": "2024-01-08T14:30:00Z",
      "end_time": "2024-01-08T15:30:00Z",
      "location": "Conference Room B",
      "attendees": [],
      "is_confirmed": true,
      "created_at": "2024-01-07T11:00:00Z"
    }
  ]
}
```

### GET /api/v1/schedule

List user's schedules.

**Query Parameters:**
- `start_date` (optional): Filter by start date
- `end_date` (optional): Filter by end date
- `limit` (optional, default: 100): Maximum number of results
- `offset` (optional, default: 0): Number of results to skip

### GET /api/v1/schedule/{schedule_id}

Get schedule by ID.

### DELETE /api/v1/schedule/{schedule_id}

Delete a schedule.

### GET /api/v1/schedule/upcoming

Get upcoming confirmed schedules.

**Query Parameters:**
- `hours` (optional, default: 24): Hours to look ahead
- `limit` (optional, default: 10): Maximum number of results

## Health Check

### GET /health

Check service health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-07T12:00:00Z",
  "services": {
    "redis": "ok",
    "milvus": "ok",
    "translation": "enabled",
    "summarization": "enabled",
    "schedule_detection": "enabled"
  }
}
```

## Error Responses

All errors follow this format:

```json
{
  "error": "ErrorType",
  "message": "Human-readable error message",
  "details": {
    // Additional error details
  }
}
```

**Common Error Codes:**
- `400`: Bad Request - Invalid input
- `401`: Unauthorized - Authentication required
- `403`: Forbidden - Insufficient permissions
- `404`: Not Found - Resource not found
- `422`: Unprocessable Entity - Validation failed
- `429`: Too Many Requests - Rate limit exceeded
- `500`: Internal Server Error - Server error
- `502`: Bad Gateway - External service error

## Examples

### cURL Examples

**Translate text:**
```bash
curl -X POST http://localhost:8000/api/v1/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, world!", "target_lang": "ko"}'
```

**Summarize document:**
```bash
curl -X POST http://localhost:8000/api/v1/summarize/document \
  -H "Content-Type: application/json" \
  -d '{"content": "Long text...", "content_type": "text"}'
```

**Detect schedule:**
```bash
curl -X POST http://localhost:8000/api/v1/schedule/detect \
  -H "Content-Type: application/json" \
  -d '{"text": "Meeting tomorrow at 3pm"}'
```

### Python Examples

```python
import requests

# Translation
response = requests.post(
    "http://localhost:8000/api/v1/translate",
    json={"text": "Hello", "target_lang": "ko"}
)
print(response.json())

# Summarization
response = requests.post(
    "http://localhost:8000/api/v1/summarize/document",
    json={"content": "Long text...", "content_type": "text"}
)
print(response.json())

# Schedule Detection
response = requests.post(
    "http://localhost:8000/api/v1/schedule/detect",
    json={"text": "Meeting tomorrow at 3pm"}
)
print(response.json())
```

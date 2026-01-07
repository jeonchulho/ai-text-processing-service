# System Architecture

## Overview

The AI Text Processing Service is a microservices-based application that provides intelligent text processing capabilities including translation, summarization, and schedule detection. The system leverages LangGraph for AI workflow orchestration, Redis for caching, and Milvus for vector similarity search.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Clients                              │
│         (Web Apps, Mobile Apps, API Consumers)              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Application                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Translation  │  │Summarization │  │   Schedule   │     │
│  │   Routes     │  │   Routes     │  │    Routes    │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│  ┌──────▼──────────────────▼──────────────────▼───────┐   │
│  │              Services Layer                         │   │
│  └──────┬──────────────────┬──────────────────┬───────┘   │
│         │                  │                  │              │
│  ┌──────▼──────────────────▼──────────────────▼───────┐   │
│  │           LangGraph Workflows                      │   │
│  │   (Translation, Summarization, Schedule)           │   │
│  └──────┬──────────────────┬──────────────────┬───────┘   │
└─────────┼──────────────────┼──────────────────┼───────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────┬──────────────┬────────────┬──────────────┐
│ PostgreSQL  │    Redis     │  Milvus    │   OpenAI     │
│ (Metadata)  │   (Cache)    │ (Vectors)  │    (LLM)     │
└─────────────┴──────────────┴────────────┴──────────────┘
```

## Components

### 1. API Layer (`src/api/`)

**FastAPI Application** - The main web framework providing RESTful API endpoints.

- **main.py**: Application setup, middleware, exception handlers
- **dependencies.py**: Dependency injection for database sessions and authentication
- **routes/**: API route handlers for each feature
  - `translation.py`: Translation endpoints
  - `summarization.py`: Summarization endpoints
  - `schedule.py`: Schedule detection endpoints

**Key Features:**
- CORS support for cross-origin requests
- Request/response logging
- Error handling and validation
- OpenAPI/Swagger documentation

### 2. Services Layer (`src/services/`)

Business logic layer that orchestrates workflows and manages database persistence.

- **translation_service.py**: Translation operations with caching
- **summarization_service.py**: Text summarization with keyword extraction
- **schedule_service.py**: Schedule detection and conflict checking
- **document_service.py**: Document parsing (PDF, DOCX, TXT)

**Responsibilities:**
- Coordinate workflow execution
- Handle database transactions
- Implement business rules
- Error handling and logging

### 3. Workflow Layer (`src/workflows/`)

LangGraph-based AI workflows that define the processing logic.

#### Translation Workflow

```
┌─────────────┐
│Check Cache  │
└──────┬──────┘
       │
       ├─ Cache Hit ────────► Return Result
       │
       └─ Cache Miss
              │
       ┌──────▼────────┐
       │ Detect Lang   │
       └──────┬────────┘
              │
       ┌──────▼────────┐
       │  Translate    │
       └──────┬────────┘
              │
       ┌──────▼────────┐
       │ Store Cache   │
       │  & Vector     │
       └──────┬────────┘
              │
       ┌──────▼────────┐
       │Return Result  │
       └───────────────┘
```

#### Summarization Workflow

```
┌─────────────┐
│   Prepare   │
│  Content    │
└──────┬──────┘
       │
┌──────▼──────┐
│    Chunk    │
│    Text     │
└──────┬──────┘
       │
┌──────▼──────┐
│   Embed     │
│  Chunks     │
└──────┬──────┘
       │
┌──────▼──────┐
│     Map     │
│ Summarize   │
└──────┬──────┘
       │
┌──────▼──────┐
│   Reduce    │
│ Summarize   │
└──────┬──────┘
       │
┌──────▼──────┐
│   Extract   │
│  Keywords   │
└──────┬──────┘
       │
┌──────▼──────┐
│Return Result│
└─────────────┘
```

#### Schedule Workflow

```
┌─────────────┐
│   Detect    │
│  Schedule   │
└──────┬──────┘
       │
       ├─ Not Found ────────► Return Result
       │
       └─ Found
              │
       ┌──────▼────────┐
       │   Extract     │
       │   Entities    │
       └──────┬────────┘
              │
       ┌──────▼────────┐
       │     Check     │
       │  Conflicts    │
       └──────┬────────┘
              │
       ┌──────▼────────┐
       │Return Result  │
       └───────────────┘
```

### 4. Repository Layer (`src/repositories/`)

Data access layer for database operations.

- **translation_repository.py**: Translation CRUD operations
- **summary_repository.py**: Summary CRUD operations
- **schedule_repository.py**: Schedule CRUD operations with conflict detection

**Pattern**: Repository pattern for clean separation of data access logic.

### 5. Models Layer (`src/models/`)

Data models and schemas.

- **database.py**: SQLAlchemy ORM models
  - `User`: User accounts
  - `Translation`: Translation history
  - `Summary`: Summarization results
  - `Schedule`: Calendar events
  - `ChatMessage`: Chat messages
  - `DirectMessage`: Direct messages

- **schemas.py**: Pydantic models for API validation
  - Request/response schemas
  - Validation rules
  - Type definitions

### 6. Utilities Layer (`src/utils/`)

Reusable utility modules.

- **redis_client.py**: Redis cache operations
- **milvus_client.py**: Milvus vector operations
- **llm_client.py**: OpenAI API wrapper
- **text_processing.py**: Text manipulation utilities

### 7. Core Layer (`src/core/`)

Core configuration and utilities.

- **config.py**: Application configuration using Pydantic Settings
- **security.py**: JWT authentication and password hashing
- **exceptions.py**: Custom exception classes

## Data Flow

### Translation Request Flow

1. **Client** sends POST request to `/api/v1/translate`
2. **API Layer** validates request using Pydantic schema
3. **Service Layer** initiates translation workflow
4. **Workflow**:
   - Checks Redis cache for existing translation
   - If miss, detects source language
   - Calls LLM for translation
   - Stores result in Redis and Milvus
5. **Repository** saves translation record to PostgreSQL
6. **API Layer** returns response to client

### Summarization Request Flow

1. **Client** sends POST request to `/api/v1/summarize/*`
2. **API Layer** validates request
3. **Service Layer** loads content from database or request
4. **Workflow**:
   - Chunks text into manageable pieces
   - Generates embeddings and stores in Milvus
   - Performs map-reduce summarization
   - Extracts keywords
5. **Repository** saves summary to PostgreSQL
6. **API Layer** returns summary and keywords

## External Services

### PostgreSQL
- **Purpose**: Primary relational database
- **Data**: User accounts, translation history, summaries, schedules
- **Connection**: SQLAlchemy ORM
- **Features**: ACID transactions, relationships, indexing

### Redis
- **Purpose**: Cache and message queue
- **Data**: Translation cache, session data
- **Features**: TTL, pub/sub, atomic operations
- **Cache Strategy**: Cache-aside pattern

### Milvus
- **Purpose**: Vector similarity search
- **Data**: Text embeddings for translations and document chunks
- **Collections**: `translations`, `document_chunks`, `summaries`
- **Index**: IVF_FLAT with L2 distance

### OpenAI
- **Purpose**: LLM and embeddings
- **Models**: 
  - GPT-4 for text generation
  - text-embedding-ada-002 for embeddings
- **Features**: Translation, summarization, entity extraction

## Scalability Considerations

### Horizontal Scaling
- **API**: Stateless design allows multiple instances behind load balancer
- **Database**: Read replicas for query distribution
- **Cache**: Redis Cluster for distributed caching
- **Vectors**: Milvus supports distributed deployment

### Performance Optimization
- **Caching**: Redis for frequently accessed translations
- **Batch Processing**: Support for batch translation requests
- **Connection Pooling**: SQLAlchemy connection pool
- **Async Operations**: FastAPI async support

### Monitoring
- **Logs**: Structured logging with structlog
- **Metrics**: Request duration, cache hit rate, error rate
- **Health Checks**: Service health endpoints

## Security

### Authentication
- JWT-based authentication
- Token expiration and refresh
- Password hashing with bcrypt

### Authorization
- Role-based access control (RBAC)
- User and superuser roles

### Data Protection
- Input validation with Pydantic
- SQL injection prevention (ORM)
- CORS configuration
- Rate limiting

## Deployment Architecture

### Docker Compose (Development)
```yaml
services:
  - postgres: Database
  - redis: Cache
  - milvus: Vector store (with etcd and minio)
  - app: FastAPI application
```

### Production (Kubernetes)
```
┌─────────────────────────────────────┐
│         Load Balancer               │
└────────────┬────────────────────────┘
             │
   ┌─────────┴─────────┐
   │                   │
┌──▼───┐          ┌───▼──┐
│ API  │          │ API  │   (Multiple replicas)
│ Pod  │          │ Pod  │
└──┬───┘          └───┬──┘
   │                   │
   └─────────┬─────────┘
             │
   ┌─────────┴─────────────┐
   │                       │
┌──▼────┐  ┌──────┐  ┌───▼───┐
│Postgres│  │Redis │  │Milvus │
└────────┘  └──────┘  └───────┘
```

## Future Enhancements

1. **WebSocket Support**: Real-time processing updates
2. **Streaming Responses**: Stream LLM output to clients
3. **Multi-Model Support**: Support for different LLM providers
4. **Advanced Caching**: Semantic caching using embeddings
5. **Calendar Integration**: Google Calendar and Outlook sync
6. **Batch Jobs**: Scheduled background processing
7. **Analytics Dashboard**: Usage metrics and insights

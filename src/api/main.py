"""
Main FastAPI application.

This module sets up the FastAPI application with all routes,
middleware, and configuration.
"""

from datetime import datetime
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog
import time

from src.core.config import settings
from src.core.exceptions import AITextProcessingException
from src.api.dependencies import create_tables
from src.api.routes import translation, summarization, schedule
from src.utils.redis_client import redis_client
from src.utils.milvus_client import milvus_client

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    AI-powered text processing and automation service built with LangGraph, Redis, and Milvus.
    
    ## Features
    
    * **Translation**: Multi-language translation with caching and vector similarity search
    * **Summarization**: Chat, message, and document summarization with keyword extraction
    * **Schedule Detection**: Natural language schedule detection with conflict checking
    
    ## Authentication
    
    For development, authentication is optional. In production, all endpoints require JWT tokens.
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing information."""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Log request
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=f"{duration:.3f}s"
    )
    
    return response


# Exception handlers
@app.exception_handler(AITextProcessingException)
async def custom_exception_handler(request: Request, exc: AITextProcessingException):
    """Handle custom application exceptions."""
    logger.error(
        "application_error",
        error=exc.message,
        status_code=exc.status_code,
        details=exc.details
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.warning(
        "validation_error",
        errors=exc.errors()
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(
        "unexpected_error",
        error=str(exc),
        exc_type=type(exc).__name__
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "details": None
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting AI Text Processing Service")
    
    # Create database tables
    try:
        create_tables()
        logger.info("Database tables initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    # Check service health
    try:
        redis_healthy = redis_client.health_check()
        logger.info(f"Redis health check: {'OK' if redis_healthy else 'FAILED'}")
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
    
    try:
        milvus_healthy = milvus_client.health_check()
        logger.info(f"Milvus health check: {'OK' if milvus_healthy else 'FAILED'}")
    except Exception as e:
        logger.warning(f"Milvus health check failed: {e}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down AI Text Processing Service")


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns status of all services.
    """
    redis_status = "ok"
    milvus_status = "ok"
    
    try:
        redis_client.health_check()
    except Exception:
        redis_status = "error"
    
    try:
        milvus_client.health_check()
    except Exception:
        milvus_status = "error"
    
    overall_status = "healthy" if (redis_status == "ok" and milvus_status == "ok") else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "redis": redis_status,
            "milvus": milvus_status,
            "translation": "enabled" if settings.ENABLE_TRANSLATION else "disabled",
            "summarization": "enabled" if settings.ENABLE_SUMMARIZATION else "disabled",
            "schedule_detection": "enabled" if settings.ENABLE_SCHEDULE_DETECTION else "disabled"
        }
    }


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint.
    
    Returns API information.
    """
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": "AI Text Processing and Automation Service",
        "docs": "/docs",
        "health": "/health"
    }


# Include routers
app.include_router(
    translation.router,
    prefix=settings.API_V1_PREFIX
)

app.include_router(
    summarization.router,
    prefix=settings.API_V1_PREFIX
)

app.include_router(
    schedule.router,
    prefix=settings.API_V1_PREFIX
)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )

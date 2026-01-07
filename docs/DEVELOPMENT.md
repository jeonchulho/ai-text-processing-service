# Development Guide

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- OpenAI API Key
- Git

### Initial Setup

1. **Clone the repository**
```bash
git clone https://github.com/jeonchulho/ai-text-processing-service.git
cd ai-text-processing-service
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

5. **Start infrastructure services**
```bash
cd docker
docker-compose up -d postgres redis milvus etcd minio
```

6. **Initialize databases**
```bash
python scripts/init_db.py
python scripts/init_milvus.py
python scripts/seed_data.py  # Optional: add sample data
```

7. **Run the application**
```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

8. **Access the API**
- API Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## Project Structure

```
ai-text-processing-service/
├── src/
│   ├── api/              # FastAPI routes and app setup
│   │   ├── main.py       # Application entry point
│   │   ├── dependencies.py
│   │   └── routes/       # API endpoints
│   ├── core/             # Core functionality
│   │   ├── config.py     # Configuration
│   │   ├── security.py   # Auth utilities
│   │   └── exceptions.py # Custom exceptions
│   ├── services/         # Business logic
│   ├── workflows/        # LangGraph workflows
│   ├── models/           # Database models and schemas
│   ├── repositories/     # Data access layer
│   └── utils/            # Utility functions
├── tests/                # Test suite
├── docker/               # Docker configuration
├── scripts/              # Utility scripts
├── docs/                 # Documentation
├── .env.example          # Environment template
├── requirements.txt      # Python dependencies
└── README.md
```

## Development Workflow

### Making Changes

1. **Create a feature branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**
- Write code following the project conventions
- Add type hints
- Include docstrings (Google style)

3. **Test your changes**
```bash
pytest tests/ -v
```

4. **Format and lint**
```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type check
mypy src/

# Lint
flake8 src/ tests/
```

5. **Commit and push**
```bash
git add .
git commit -m "feat: add your feature"
git push origin feature/your-feature-name
```

6. **Create pull request**

### Code Style

#### Python Style Guide
- Follow PEP 8
- Use type hints for all functions
- Maximum line length: 100 characters
- Use Google-style docstrings

#### Example Function
```python
def process_text(
    text: str,
    max_length: int = 1000
) -> dict:
    """
    Process text with specified constraints.

    Args:
        text: Input text to process
        max_length: Maximum allowed length

    Returns:
        Dictionary containing processed result

    Raises:
        ValidationError: If text is invalid
    """
    # Implementation
    pass
```

#### Naming Conventions
- **Classes**: PascalCase (`TranslationService`)
- **Functions/Methods**: snake_case (`translate_text`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_BATCH_SIZE`)
- **Private**: Prefix with underscore (`_internal_method`)

### Testing

#### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_translation.py

# Run with coverage
pytest --cov=src tests/

# Run with verbose output
pytest -v
```

#### Writing Tests
```python
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_translate_endpoint():
    """Test translation endpoint."""
    response = client.post(
        "/api/v1/translate",
        json={
            "text": "Hello",
            "target_lang": "ko"
        }
    )
    
    assert response.status_code == 200
    assert "translated_text" in response.json()
```

### Database Migrations

#### Using Alembic

1. **Create migration**
```bash
alembic revision --autogenerate -m "Add new column"
```

2. **Apply migration**
```bash
alembic upgrade head
```

3. **Rollback migration**
```bash
alembic downgrade -1
```

### Docker Development

#### Using Docker Compose

**Start all services:**
```bash
docker-compose up -d
```

**View logs:**
```bash
docker-compose logs -f app
```

**Rebuild after changes:**
```bash
docker-compose up -d --build
```

**Stop services:**
```bash
docker-compose down
```

**Remove volumes:**
```bash
docker-compose down -v
```

### Debugging

#### Local Debugging
```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use built-in breakpoint()
breakpoint()
```

#### VS Code Debugging
Create `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "src.api.main:app",
                "--reload",
                "--host", "0.0.0.0",
                "--port", "8000"
            ],
            "jinja": true
        }
    ]
}
```

### Environment Variables

#### Required Variables
```env
OPENAI_API_KEY=sk-xxx          # Required for LLM operations
DATABASE_URL=postgresql://...   # PostgreSQL connection
REDIS_URL=redis://...          # Redis connection
MILVUS_HOST=localhost          # Milvus host
MILVUS_PORT=19530              # Milvus port
```

#### Optional Variables
```env
JWT_SECRET_KEY=your-secret     # For authentication
LOG_LEVEL=INFO                 # Logging level
MAX_WORKERS=4                  # Worker threads
REDIS_CACHE_TTL=3600          # Cache expiration
```

## Adding New Features

### Adding a New Service

1. **Create service file** (`src/services/new_service.py`)
```python
from sqlalchemy.orm import Session
import structlog

logger = structlog.get_logger(__name__)

class NewService:
    """Service for new feature."""

    def __init__(self, db: Session):
        self.db = db

    async def process(self, data: dict) -> dict:
        """Process data."""
        # Implementation
        pass
```

2. **Create workflow** (`src/workflows/new_workflow.py`)
```python
from typing import TypedDict
from langgraph.graph import StateGraph, END

class NewState(TypedDict):
    """State for new workflow."""
    input: str
    output: str

def process_node(state: NewState) -> NewState:
    """Process node."""
    # Implementation
    return state

def create_new_workflow() -> StateGraph:
    """Create workflow."""
    workflow = StateGraph(NewState)
    workflow.add_node("process", process_node)
    workflow.set_entry_point("process")
    workflow.add_edge("process", END)
    return workflow.compile()

new_workflow = create_new_workflow()
```

3. **Create routes** (`src/api/routes/new_route.py`)
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.api.dependencies import get_db

router = APIRouter(prefix="/new", tags=["new"])

@router.post("/")
async def process(
    data: dict,
    db: Session = Depends(get_db)
):
    """Process endpoint."""
    # Implementation
    pass
```

4. **Register routes** in `src/api/main.py`
```python
from src.api.routes import new_route

app.include_router(
    new_route.router,
    prefix=settings.API_V1_PREFIX
)
```

### Adding Database Model

1. **Add model** in `src/models/database.py`
```python
class NewModel(Base):
    """New model."""
    __tablename__ = "new_table"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
```

2. **Add schema** in `src/models/schemas.py`
```python
class NewModelRequest(BaseModel):
    """Request schema."""
    name: str

class NewModelResponse(BaseModel):
    """Response schema."""
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True
```

3. **Create repository**
```python
class NewRepository:
    """Repository for new model."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, name: str) -> NewModel:
        """Create record."""
        model = NewModel(name=name)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model
```

## Troubleshooting

### Common Issues

**Issue: OpenAI API Key Error**
```
Solution: Ensure OPENAI_API_KEY is set in .env file
```

**Issue: Database Connection Error**
```
Solution: Verify PostgreSQL is running
docker-compose ps postgres
```

**Issue: Redis Connection Error**
```
Solution: Check Redis service
docker-compose ps redis
```

**Issue: Milvus Connection Error**
```
Solution: Milvus requires etcd and minio to be running
docker-compose up -d etcd minio
```

### Logs

**View application logs:**
```bash
docker-compose logs -f app
```

**View PostgreSQL logs:**
```bash
docker-compose logs -f postgres
```

**View all service logs:**
```bash
docker-compose logs -f
```

## Best Practices

### Code Organization
- Keep files focused on single responsibility
- Use dependency injection
- Separate business logic from API logic
- Use repository pattern for data access

### Error Handling
- Use custom exceptions
- Log errors with context
- Return meaningful error messages
- Handle edge cases

### Performance
- Use async/await for I/O operations
- Implement caching where appropriate
- Use database indexes
- Batch operations when possible

### Security
- Never commit secrets
- Validate all inputs
- Use parameterized queries
- Implement rate limiting

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)

## Support

For questions or issues:
1. Check existing documentation
2. Search closed issues on GitHub
3. Open a new issue with details

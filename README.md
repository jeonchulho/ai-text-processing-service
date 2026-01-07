# AI Text Processing Service

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AI-powered text processing and automation service built with **LangGraph**, **Redis**, and **Milvus**. This service provides intelligent translation, summarization, and schedule detection capabilities through a RESTful API.

## 🌟 Features

### 📝 Translation Service
- Multi-language translation (Korean ↔ English ↔ Japanese ↔ Chinese)
- Context-aware translation using LLM
- Redis caching for fast responses
- Vector-based similar translation search with Milvus
- Batch translation support

### 📄 Summarization Service
- Chat conversation summarization
- Direct message (쪽지) summarization
- Document summarization (PDF, DOCX, TXT)
- Automatic keyword extraction
- Map-Reduce strategy for long documents

### 📅 Schedule Detection Service
- Natural language schedule detection
- Entity extraction (date, time, location, attendees)
- Schedule conflict detection
- Calendar API integration ready (Google Calendar, Outlook)

## 🏗️ Architecture

### Technology Stack

- **Backend Framework**: FastAPI
- **AI Orchestration**: LangGraph
- **Caching & Queue**: Redis
- **Vector Database**: Milvus
- **Relational Database**: PostgreSQL
- **LLM Provider**: OpenAI GPT-4
- **Embeddings**: OpenAI Embeddings

### System Components

```
┌─────────────┐
│   FastAPI   │  ← REST API Layer
└──────┬──────┘
       │
┌──────▼──────────────────────────┐
│   LangGraph Workflows           │  ← AI Orchestration
│  - Translation Workflow          │
│  - Summarization Workflow        │
│  - Schedule Detection Workflow   │
└──────┬──────────────────────────┘
       │
┌──────▼──────┬──────────┬────────┐
│  PostgreSQL │  Redis   │ Milvus │  ← Data Layer
│  (Metadata) │ (Cache)  │(Vector)│
└─────────────┴──────────┴────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- OpenAI API Key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/jeonchulho/ai-text-processing-service.git
cd ai-text-processing-service
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

3. **Start services with Docker Compose**
```bash
cd docker
docker-compose up -d
```

4. **Initialize databases**
```bash
python scripts/init_db.py
python scripts/init_milvus.py
```

5. **Access the API**
- API Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## 🐳 Docker Compose Services

The `docker-compose.yml` includes:
- **PostgreSQL**: Metadata storage (port 5432)
- **Redis**: Caching and message queue (port 6379)
- **Milvus**: Vector database (port 19530)
- **FastAPI**: Backend API (port 8000)

## 📚 API Endpoints

### Translation
- `POST /api/v1/translate` - Translate text
- `POST /api/v1/translate/batch` - Batch translation
- `GET /api/v1/translate/history` - Translation history

### Summarization
- `POST /api/v1/summarize/chat` - Summarize chat conversation
- `POST /api/v1/summarize/message` - Summarize direct message
- `POST /api/v1/summarize/document` - Summarize document
- `GET /api/v1/summarize/keywords/{summary_id}` - Get keywords

### Schedule
- `POST /api/v1/schedule/detect` - Detect schedule from text
- `POST /api/v1/schedule/confirm` - Confirm and create schedule
- `GET /api/v1/schedule/conflicts` - Check schedule conflicts
- `DELETE /api/v1/schedule/{schedule_id}` - Delete schedule

## 💻 Development

### Local Development Setup

1. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run development server**
```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Project Structure

```
ai-text-processing-service/
├── src/
│   ├── api/              # FastAPI routes and dependencies
│   ├── core/             # Core configuration and security
│   ├── services/         # Business logic services
│   ├── workflows/        # LangGraph workflows
│   ├── models/           # Database models and schemas
│   ├── repositories/     # Data access layer
│   └── utils/            # Utility functions and clients
├── tests/                # Test suite
├── docker/               # Docker configuration
├── scripts/              # Initialization scripts
├── docs/                 # Documentation
├── .env.example          # Environment template
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/ tests/
```

## 📖 Documentation

- [API Documentation](docs/API.md) - Detailed API reference
- [Architecture](docs/ARCHITECTURE.md) - System architecture and design
- [Development Guide](docs/DEVELOPMENT.md) - Developer guide
- [PRD](docs/PRD.md) - Product Requirements Document

## 🔐 Security

- JWT-based authentication
- API rate limiting
- Input validation with Pydantic
- SQL injection prevention
- Environment-based configuration

## 🎯 Roadmap

### Phase 1: MVP (Current)
- ✅ Core translation service
- ✅ Basic summarization
- ✅ Schedule detection

### Phase 2: Enhancement
- [ ] Multi-model LLM support
- [ ] Advanced caching strategies
- [ ] Real-time processing with WebSocket
- [ ] Enhanced NER for schedule detection

### Phase 3: Integration
- [ ] Google Calendar integration
- [ ] Outlook Calendar integration
- [ ] Slack bot integration
- [ ] Microsoft Teams integration

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Jeon Chul Ho** - Initial work

## 🙏 Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) - AI workflow orchestration
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Milvus](https://milvus.io/) - Vector database
- [Redis](https://redis.io/) - In-memory data store

## 📧 Contact

For questions and support, please open an issue on GitHub.

---

**Built with ❤️ using LangGraph, Redis, and Milvus**
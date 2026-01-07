# Quick Start Guide

## Prerequisites

- Docker and Docker Compose installed
- OpenAI API Key
- At least 4GB RAM available

## Getting Started in 5 Minutes

### Step 1: Clone and Setup

```bash
git clone https://github.com/jeonchulho/ai-text-processing-service.git
cd ai-text-processing-service
cp .env.example .env
```

### Step 2: Add OpenAI API Key

Edit `.env` file and add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-actual-key-here
```

### Step 3: Start Services

```bash
cd docker
docker-compose up -d
```

Wait for all services to start (about 1-2 minutes).

### Step 4: Initialize Database

```bash
# In a new terminal
docker-compose exec app python scripts/init_db.py
docker-compose exec app python scripts/init_milvus.py
docker-compose exec app python scripts/seed_data.py
```

### Step 5: Test the API

Open your browser and visit:
- **Swagger UI**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

Try the translation endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, world!", "target_lang": "ko"}'
```

## What's Available?

### Services Running
- **FastAPI**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Milvus**: localhost:19530
- **Minio Console**: http://localhost:9001

### API Features
- ✅ Translation (Korean, English, Japanese, Chinese)
- ✅ Summarization (Chat, Message, Document)
- ✅ Schedule Detection from natural language

### Test Credentials
- **Username**: test_user
- **Password**: test_password

## Next Steps

1. **Read the Documentation**
   - [API Documentation](docs/API.md)
   - [Architecture](docs/ARCHITECTURE.md)
   - [Development Guide](docs/DEVELOPMENT.md)

2. **Try More Examples**
   - Batch translation
   - Document summarization
   - Schedule detection

3. **Customize**
   - Adjust cache TTL
   - Configure rate limits
   - Add more features

## Troubleshooting

**Services won't start?**
```bash
docker-compose down -v
docker-compose up -d --force-recreate
```

**Check service logs:**
```bash
docker-compose logs -f app
```

**Check all services are healthy:**
```bash
docker-compose ps
```

All services should show "healthy" status.

## Stopping Services

```bash
docker-compose down
```

To remove all data:
```bash
docker-compose down -v
```

## Support

- 📖 [Full Documentation](README.md)
- 🐛 [Report Issues](https://github.com/jeonchulho/ai-text-processing-service/issues)
- 💬 [Discussions](https://github.com/jeonchulho/ai-text-processing-service/discussions)

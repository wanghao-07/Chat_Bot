# Chat Bot - Architecture Documentation

## System Design

Chat Bot is a production-ready AI customer service system built on a layered architecture:

```
Presentation Layer  : HTML/CSS/JS Frontend
API Layer           : FastAPI REST endpoints
Service Layer       : Business logic orchestration
Data Layer          : SQLite + FAISS
External Layer      : Qwen Max API (DashScope)
```

## Core Components

### 1. Orchestrator (app/core/orchestrator.py)
Central conversation controller that coordinates:
- LLM service for AI response generation
- RAG service for knowledge base retrieval
- Memory service for conversation context
- Prompt assembly with configurable system prompts

### 2. RAG Pipeline (app/rag/)
Document ingestion and retrieval-augmented generation flow:

```
Document Upload -> Text Extraction -> Chunking -> FAISS Embedding -> Vector Storage
                                                       |
User Query -> Embedding -> FAISS Search -> Top K Chunks -> Context Assembly -> LLM Generation
```

### 3. Memory Service (app/services/memory_service.py)
SQLite-based conversation memory:
- Session-scoped message history
- Configurable context window (last N messages)
- Automatic session cleanup

### 4. Config Service (app/services/config_service.py)
Runtime configuration management:
- Brand name and tone customization
- System prompt templates
- Temperature and model parameters

## API Design

### POST /api/v1/chat
Main chat endpoint. Accepts user message, returns AI response with RAG context.

Request: `{ "message": "...", "session_id": "..." }`
Response: `{ "response": "...", "session_id": "...", "sources": [...] }`

### POST /api/v1/knowledge/upload
Document upload for knowledge base enrichment.

### GET /api/v1/health
Health check returning service status.

## Deployment

### Local Development
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker
```bash
docker build -t chat-bot .
docker run -p 8000:8000 -e DASHSCOPE_API_KEY=xxx chat-bot
```

## Security Considerations
- API keys managed via environment variables
- Input validation on all endpoints
- SQL injection protection via ORM
- CORS configuration for frontend access control

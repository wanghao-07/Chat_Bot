# Chat Bot - AI Customer Service Robot

> Powered by Qwen Max (DashScope), featuring web chat interface, conversation memory, knowledge base RAG (FAISS), and configurable brand prompts.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal.svg)](https://fastapi.tiangolo.com/)
[![Qwen](https://img.shields.io/badge/LLM-Qwen_Max-purple.svg)](https://dashscope.aliyun.com/)
[![Stars](https://img.shields.io/github/stars/wanghao-07/Chat_Bot.svg)](https://github.com/wanghao-07/Chat_Bot/stargazers)

---

## Features

- **AI Conversation**: Qwen Max (DashScope) powered, multi-turn context memory (SQLite)
- **RAG Knowledge Base**: Upload PDF/TXT/MD, auto chunking + vectorization + retrieval-augmented answers
- **Configurable**: Brand name, business description, tone, custom System Prompt (API + frontend settings page)
- **Production Ready**: Structured logging, unified error responses, health checks, knowledge base management
- **Web Chat Interface**: Clean frontend with real-time streaming

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Alibaba Cloud DashScope API Key

### 2. Setup

```bash
cd Chatbot
copy .env.example .env
# Edit .env with your DASHSCOPE_API_KEY

python -m venv .venv
.venv\\Scripts\\activate
pip install -r backend\\requirements.txt
```

### 3. Run

```bash
# Windows
.\\run.ps1

# Or directly
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 in your browser.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat` | Send message, get AI response |
| GET | `/api/v1/sessions` | List conversation sessions |
| POST | `/api/v1/knowledge/upload` | Upload document to knowledge base |
| DELETE | `/api/v1/knowledge/{id}` | Remove from knowledge base |
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/config` | Get/update bot configuration |

## Project Structure

```
Chatbot/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI entry
│       ├── config.py            # Configuration
│       ├── api/v1/              # API routes
│       │   ├── chat.py          # Chat endpoint
│       │   ├── sessions.py      # Session management
│       │   ├── knowledge.py     # Knowledge base API
│       │   ├── config.py        # Configuration API
│       │   └── health.py        # Health checks
│       ├── core/
│       │   ├── orchestrator.py  # Main conversation orchestrator
│       │   ├── prompts.py       # Prompt templates
│       │   └── exceptions.py    # Custom exceptions
│       ├── models/
│       │   ├── session.py       # Session model
│       │   ├── message.py       # Message model
│       │   ├── document.py      # Document model
│       │   └── schemas.py       # Pydantic schemas
│       ├── services/
│       │   ├── llm_service.py   # LLM integration
│       │   ├── rag_service.py   # RAG pipeline
│       │   ├── memory_service.py# Conversation memory
│       │   ├── ingest_service.py# Document ingestion
│       │   └── config_service.py# Configuration service
│       ├── rag/
│       │   ├── chunker.py       # Document chunking
│       │   └── vector_store.py  # FAISS vector store
│       └── repositories/        # Data access layer
├── frontend/
│   ├── index.html               # Chat interface
│   ├── app.js                   # Frontend logic
│   └── styles.css               # Styles
├── data/
│   └── chatbot.db               # SQLite database
└── run.ps1                      # Startup script
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| LLM | Qwen Max (DashScope) |
| Backend | FastAPI + Uvicorn |
| Vector Store | FAISS |
| Database | SQLite |
| Frontend | Vanilla HTML/JS/CSS |

## Architecture

```
User Browser
    |
    v
FastAPI Server
    ├── Chat Endpoint ──> Orchestrator ──> LLM Service ──> Qwen Max API
    ├── Knowledge API ──> Ingest Service ──> Chunker ──> FAISS Vector Store
    ├── Session API  ──> Memory Service ──> SQLite
    └── Config API   ──> Config Service
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Related Projects

- [AgentFlow](https://github.com/wanghao-07/AgentFlow) - Multi-Agent Collaborative Document Analysis Platform
- [little-assistant](https://github.com/wanghao-07/little-assistant) - Enterprise RAG Q&A System

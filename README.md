# CodeMentor AI 🧠

A **RAG-based GenAI application** that helps developers understand unfamiliar GitHub repositories using Retrieval Augmented Generation.

## What It Does

1. **Submit** a GitHub repository URL
2. **Ask questions** like "How does authentication work?" or "Explain the project architecture"
3. **Get accurate answers** with source citations pointing to exact files and line numbers
4. **Generate onboarding docs** automatically for any repository

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite + TailwindCSS |
| Backend | FastAPI (Python) |
| Vector DB | Qdrant Cloud |
| LLM | Qwen via OpenRouter |
| Embeddings | BAAI/bge-small-en-v1.5 |
| Cache | Redis |
| Proxy | Nginx |
| Container | Docker |

## Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/parinbajayebin/Codementor.ai.git
cd Codementor.ai
```

### 2. Set up environment
```bash
cp .env.example .env
# Fill in your API keys in .env
```

### 3. Run the backend
```bash
cd backend
python -m venv .venv
.venv/Scripts/activate  # Windows
# source .venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4. View API docs
Open [http://localhost:8000/docs](http://localhost:8000/docs) for Swagger documentation.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | OpenRouter API key for LLM access |
| `QDRANT_URL` | Phase 2+ | Qdrant Cloud cluster URL |
| `QDRANT_API_KEY` | Phase 2+ | Qdrant Cloud API key |
| `HF_TOKEN` | Optional | HuggingFace access token |
| `REDIS_URL` | Optional | Redis connection URL (default: localhost:6379) |

## Project Status

**Current Phase:** Phase 1 — Repository Ingestion Foundation ✅

See `project-management/ROADMAP.md` for full roadmap.

## License

MIT

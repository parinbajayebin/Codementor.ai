"""
main.py - FastAPI application entry point for CodeMentor AI

This is where the FastAPI app is created, configured, and routes are registered.
Run with: uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import repository, chat
from app.utils.cache import cache
from app.utils.logger import get_logger
from app.models.responses import HealthResponse

logger = get_logger(__name__)

# ------------------------------------------------------------------
# Create the FastAPI application
# ------------------------------------------------------------------
app = FastAPI(
    title="CodeMentor AI",
    description=(
        "A RAG-based GenAI API that helps developers understand "
        "unfamiliar GitHub repositories. Submit a repo URL, ask questions, "
        "and get cited answers grounded in actual source code."
    ),
    version="0.1.0",
)

# ------------------------------------------------------------------
# CORS Middleware - allows frontend to call backend
# ------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Register route modules
# ------------------------------------------------------------------
app.include_router(repository.router)
app.include_router(chat.router)

# Phase 2+: Will add onboarding router here
# app.include_router(onboarding.router)


# ------------------------------------------------------------------
# Health check endpoint
# ------------------------------------------------------------------
@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """
    Health check endpoint.

    Returns app status and whether Redis is connected.
    Useful for monitoring and deployment verification.
    """
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        redis_connected=cache.is_connected,
    )


# ------------------------------------------------------------------
# Startup event
# ------------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    """
    Runs when the server starts.
    Logs configuration info (without exposing secrets).
    """
    logger.info("=" * 50)
    logger.info("CodeMentor AI - Starting up")
    logger.info("=" * 50)
    logger.info(f"Embedding model: {settings.embedding_model}")
    logger.info(f"LLM model: {settings.llm_model}")
    logger.info(f"Qdrant collection: {settings.collection_name}")
    logger.info(f"Redis connected: {cache.is_connected}")
    logger.info(f"Max file size: {settings.max_file_size} bytes")
    logger.info(f"Max files per repo: {settings.max_files_per_repo}")
    logger.info(f"Chunk size: {settings.chunk_size} chars")
    logger.info(f"Top-K retrieval: {settings.top_k}")
    logger.info("=" * 50)

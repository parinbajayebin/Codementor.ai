"""
responses.py - Pydantic models for API responses

Every response from the API follows one of these shapes.
This ensures consistent, predictable JSON for the frontend.
"""

from typing import Optional
from pydantic import BaseModel


class RepositoryInfo(BaseModel):
    """Basic information about an ingested repository."""
    repo_id: str
    repo_name: str
    owner: str
    github_url: str
    total_files: int
    total_chunks: int
    status: str  # "processing", "completed", "failed"


class IngestResponse(BaseModel):
    """Response for POST /api/repository/ingest"""
    message: str
    repo_id: str
    status: str


class FileInfo(BaseModel):
    """Information about a single parsed file."""
    file_path: str
    language: str
    size_bytes: int


class ParsedRepositoryResponse(BaseModel):
    """Response showing parsed repository details."""
    repo_id: str
    total_files: int
    files: list[FileInfo]
    skipped_files: int
    skipped_reasons: list[str]


class StatusResponse(BaseModel):
    """Response for GET /api/repository/{repo_id}/status"""
    repo_id: str
    status: str  # "processing", "completed", "failed"
    total_files: int
    total_chunks: int
    message: str


class ErrorResponse(BaseModel):
    """Standard error response shape."""
    error: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    """Response for GET /api/health"""
    status: str
    version: str
    redis_connected: bool


class Citation(BaseModel):
    """A citation mapping to a specific code source chunk."""
    source_number: int
    file_path: str
    start_line: int
    end_line: int
    content_preview: str
    language: Optional[str] = "text"
    relevance_score: float
    confidence: str  # "high", "medium", "low"


class AskQuestionResponse(BaseModel):
    """Response for POST /api/chat/ask"""
    repo_id: str
    question: str
    answer: str
    citations: list[Citation]


class ChatMessage(BaseModel):
    """A single message in the chat history."""
    role: str  # "user" or "assistant"
    content: str
    citations: Optional[list[Citation]] = None
    timestamp: float


class ChatHistoryResponse(BaseModel):
    """Response for GET /api/chat/{repo_id}/history"""
    repo_id: str
    messages: list[ChatMessage]


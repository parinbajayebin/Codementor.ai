"""
chat.py - API routes for chat interaction

Endpoints:
    POST /api/chat/ask             - Ask a question about a repository
    GET  /api/chat/{id}/history    - Get chat history for a repository
    DELETE /api/chat/{id}/history  - Clear chat history for a repository
"""

import time
from fastapi import APIRouter, HTTPException

from app.models.requests import AskQuestionRequest
from app.models.responses import (
    AskQuestionResponse,
    ChatHistoryResponse,
    ChatMessage,
    ErrorResponse,
)
from app.services import (
    retrieval_service,
    llm_service,
    citation_service,
    vector_service,
)
from app.utils.cache import cache
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Create a router with the /api/chat prefix
router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post(
    "/ask",
    response_model=AskQuestionResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def ask_question(request: AskQuestionRequest):
    """
    Ask a question about an ingested repository.

    RAG Pipeline:
    1. Verify the repository exists in our system.
    2. Fetch chat history to maintain conversation context.
    3. Retrieve relevant code chunks from Qdrant using semantic search.
    4. Format the context and call Qwen LLM via OpenRouter.
    5. Parse and extract citations from the LLM answer.
    6. Save the new messages (user and assistant) to the chat history.
    """
    repo_id = request.repo_id
    question = request.question

    logger.info(f"Chat request for repo '{repo_id}': {question[:50]}...")

    # Step 1: Verify repository exists (check cache first, fallback to Qdrant)
    repo_exists = False
    repo_status = cache.get(f"repo:status:{repo_id}")
    if repo_status and repo_status.get("status") == "completed":
        repo_exists = True
    else:
        # Fallback if cache is cleared/disabled
        repo_exists = vector_service.check_repo_exists(repo_id)

    if not repo_exists:
        raise HTTPException(
            status_code=404,
            detail=f"Repository '{repo_id}' not found or is not fully ingested. "
                   f"Ingest the repo first via /api/repository/ingest",
        )

    try:
        # Step 2: Fetch chat history (to pass context to LLM)
        history_key = f"chat:history:{repo_id}"
        cached_history = cache.get(history_key) or []

        # Convert cached message list format for LLM context
        llm_history = []
        for msg in cached_history:
            llm_history.append({
                "role": msg.get("role"),
                "content": msg.get("content"),
            })

        # Step 3: Retrieve relevant code chunks
        retrieved_chunks = retrieval_service.search_repository(
            question=question,
            repo_id=repo_id,
        )

        if not retrieved_chunks:
            logger.warning(f"No code chunks retrieved for query on repo '{repo_id}'")

        # Step 4: Format context and generate LLM response
        context_str = retrieval_service.format_context_for_llm(retrieved_chunks)
        answer = llm_service.generate_answer(
            question=question,
            context=context_str,
            chat_history=llm_history,
        )

        # Step 5: Extract citations used by the LLM
        citations = citation_service.extract_citations(
            answer=answer,
            retrieved_chunks=retrieved_chunks,
        )

        # Step 6: Update chat history in cache
        user_message = {
            "role": "user",
            "content": question,
            "citations": None,
            "timestamp": time.time(),
        }

        assistant_message = {
            "role": "assistant",
            "content": answer,
            "citations": [c.model_dump() for c in citations],
            "timestamp": time.time(),
        }

        cached_history.append(user_message)
        cached_history.append(assistant_message)

        # Keep history length under control (last 20 messages = 10 rounds of chat)
        if len(cached_history) > 20:
            cached_history = cached_history[-20:]

        cache.set(history_key, cached_history, ttl_seconds=86400)  # 24 hour history TTL

        return AskQuestionResponse(
            repo_id=repo_id,
            question=question,
            answer=answer,
            citations=citations,
        )

    except Exception as error:
        logger.error(f"Error in chat processing for {repo_id}: {error}")
        raise HTTPException(status_code=500, detail=str(error))


@router.get(
    "/{repo_id}/history",
    response_model=ChatHistoryResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_chat_history(repo_id: str):
    """Get the conversation history for a specific repository."""
    # Verify repo exists
    repo_exists = False
    repo_status = cache.get(f"repo:status:{repo_id}")
    if repo_status and repo_status.get("status") == "completed":
        repo_exists = True
    else:
        repo_exists = vector_service.check_repo_exists(repo_id)

    if not repo_exists:
        raise HTTPException(
            status_code=404,
            detail=f"Repository '{repo_id}' not found",
        )

    history_key = f"chat:history:{repo_id}"
    history_data = cache.get(history_key) or []

    # Map raw cached dicts to ChatMessage models
    messages = []
    for msg in history_data:
        citations_data = msg.get("citations")
        citations = None
        if citations_data:
            citations = [c for c in citations_data]

        messages.append(
            ChatMessage(
                role=msg.get("role"),
                content=msg.get("content"),
                citations=citations,
                timestamp=msg.get("timestamp", time.time()),
            )
        )

    return ChatHistoryResponse(repo_id=repo_id, messages=messages)


@router.delete(
    "/{repo_id}/history",
    responses={404: {"model": ErrorResponse}},
)
def clear_chat_history(repo_id: str):
    """Clear conversation history for a specific repository."""
    # Verify repo exists
    repo_exists = False
    repo_status = cache.get(f"repo:status:{repo_id}")
    if repo_status and repo_status.get("status") == "completed":
        repo_exists = True
    else:
        repo_exists = vector_service.check_repo_exists(repo_id)

    if not repo_exists:
        raise HTTPException(
            status_code=404,
            detail=f"Repository '{repo_id}' not found",
        )

    history_key = f"chat:history:{repo_id}"
    cache.delete(history_key)

    logger.info(f"Cleared chat history for: {repo_id}")
    return {"message": f"Chat history for repository '{repo_id}' cleared"}


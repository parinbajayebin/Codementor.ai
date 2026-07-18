"""
retrieval_service.py - Find relevant code chunks for a question

This service connects the embedding and vector services:
1. Takes a user question
2. Converts it to an embedding
3. Searches Qdrant for similar code chunks
4. Returns ranked results with metadata

This is the "R" in RAG — the retrieval step.
"""

from app.services import embedding_service, vector_service
from app.utils.cache import cache
from app.utils.logger import get_logger

import hashlib

logger = get_logger(__name__)


def search_repository(
    question: str,
    repo_id: str,
    top_k: int = None,
) -> list[dict]:
    """
    Search a repository for code chunks relevant to a question.

    Steps:
    1. Check cache for this exact question+repo combo
    2. Embed the question using the same model used for chunks
    3. Search Qdrant for nearest vectors, filtered by repo_id
    4. Cache and return results

    Args:
        question: The user's question (e.g., "How does auth work?")
        repo_id: Which repository to search in
        top_k: Number of results (default from settings)

    Returns:
        List of matching chunks with scores, sorted by relevance
    """
    # Step 1: Check cache
    question_hash = hashlib.md5(f"{repo_id}:{question}".encode()).hexdigest()[:12]
    cache_key = f"search:{repo_id}:{question_hash}"

    cached_results = cache.get(cache_key)
    if cached_results is not None:
        logger.info(f"Search cache hit for: {question[:50]}...")
        return cached_results

    # Step 2: Embed the question
    logger.info(f"Embedding question: {question[:80]}...")
    question_embedding = embedding_service.generate_embedding(question)

    # Step 3: Search Qdrant
    results = vector_service.search_similar_chunks(
        query_embedding=question_embedding,
        repo_id=repo_id,
        top_k=top_k,
    )

    # Step 4: Cache results (10 minute TTL)
    cache.set(cache_key, results, ttl_seconds=600)

    logger.info(f"Search complete: {len(results)} results for '{question[:50]}...'")
    return results


def format_context_for_llm(search_results: list[dict]) -> str:
    """
    Format retrieved chunks into a context string for the LLM prompt.

    Each chunk is labeled with a source number so the LLM can
    reference it in its answer (e.g., "[Source 1]").

    Args:
        search_results: List of search result dicts from search_repository

    Returns:
        A formatted string ready to be inserted into an LLM prompt
    """
    if not search_results:
        return "No relevant code was found for this question."

    context_parts = []

    for i, result in enumerate(search_results, 1):
        file_path = result["file_path"]
        start_line = result["start_line"]
        end_line = result["end_line"]
        language = result["language"]
        content = result["content"]
        score = result["score"]

        source_header = (
            f"[Source {i}: {file_path} L{start_line}-{end_line}] "
            f"(relevance: {score:.2f})"
        )

        context_parts.append(
            f"{source_header}\n"
            f"```{language}\n"
            f"{content}\n"
            f"```\n"
        )

    return "\n".join(context_parts)

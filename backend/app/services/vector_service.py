"""
vector_service.py - Qdrant vector database operations

Handles all interactions with Qdrant Cloud:
    - Create collection (once)
    - Store code chunk vectors with metadata
    - Search for similar vectors
    - Delete vectors for a repository

Uses a single collection "code_chunks" with payload filtering
to separate different repositories.
"""

import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    PayloadSchemaType,
)

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Module-level client — created once, reused
_client = None


def get_qdrant_client() -> QdrantClient:
    """
    Get or create the Qdrant client connection.

    Raises an error if Qdrant credentials are not configured.
    """
    global _client

    if _client is not None:
        return _client

    if not settings.qdrant_url or not settings.qdrant_api_key:
        raise Exception(
            "Qdrant credentials not configured. "
            "Set QDRANT_URL and QDRANT_API_KEY in your .env file."
        )

    logger.info(f"Connecting to Qdrant at: {settings.qdrant_url[:30]}...")

    _client = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        timeout=30,
    )

    logger.info("Qdrant client connected")
    return _client


def ensure_collection_exists():
    """
    Create the code_chunks collection if it doesn't exist.

    Collection config:
        - Vector size: 384 (matching bge-small-en-v1.5)
        - Distance: Cosine similarity
    """
    client = get_qdrant_client()
    collection_name = settings.collection_name

    # Check if collection already exists
    collections = client.get_collections().collections
    existing_names = [c.name for c in collections]

    if collection_name in existing_names:
        logger.info(f"Collection '{collection_name}' already exists")
        # Ensure payload index exists (safe to call even if it already exists)
        try:
            client.create_payload_index(
                collection_name=collection_name,
                field_name="repo_id",
                field_schema=PayloadSchemaType.KEYWORD,
            )
        except Exception:
            pass  # Index already exists, that's fine
        return

    # Create the collection
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=settings.embedding_dimension,  # 384 for bge-small
            distance=Distance.COSINE,
        ),
    )
    logger.info(f"Created collection '{collection_name}' (dim={settings.embedding_dimension})")

    # Create payload index on repo_id for fast filtered search
    client.create_payload_index(
        collection_name=collection_name,
        field_name="repo_id",
        field_schema=PayloadSchemaType.KEYWORD,
    )
    logger.info("Created payload index on 'repo_id'")


def store_vectors(
    chunks: list,
    embeddings: list[list[float]],
) -> int:
    """
    Store code chunk vectors and their metadata in Qdrant.

    Each chunk becomes a "point" in Qdrant with:
        - A unique UUID
        - The embedding vector
        - A payload containing file_path, content, line numbers, etc.

    Args:
        chunks: List of CodeChunk objects
        embeddings: List of embedding vectors (same order as chunks)

    Returns:
        Number of points stored
    """
    client = get_qdrant_client()
    ensure_collection_exists()

    # Build Qdrant points
    points = []
    for chunk, embedding in zip(chunks, embeddings):
        point = PointStruct(
            id=str(uuid.uuid4()),  # Unique ID for each point
            vector=embedding,
            payload=chunk.to_payload(),
        )
        points.append(point)

    # Upsert in batches of 100 (Qdrant handles large batches well)
    batch_size = 100
    total_stored = 0

    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        client.upsert(
            collection_name=settings.collection_name,
            points=batch,
        )
        total_stored += len(batch)
        logger.info(f"Stored batch {i // batch_size + 1}: {total_stored}/{len(points)} points")

    logger.info(f"Total vectors stored: {total_stored}")
    return total_stored


def search_similar_chunks(
    query_embedding: list[float],
    repo_id: str,
    top_k: int = None,
) -> list[dict]:
    """
    Find the most similar code chunks to a query embedding.

    Filters by repo_id so results only come from the target repository.

    Args:
        query_embedding: The embedding vector of the user's question
        repo_id: Only search within this repository
        top_k: Number of results to return (default from settings)

    Returns:
        List of dicts with keys: content, file_path, start_line,
        end_line, language, score
    """
    if top_k is None:
        top_k = settings.top_k

    client = get_qdrant_client()

    # Search with repo_id filter
    search_results = client.search(
        collection_name=settings.collection_name,
        query_vector=query_embedding,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="repo_id",
                    match=MatchValue(value=repo_id),
                )
            ]
        ),
        limit=top_k,
    )

    # Convert Qdrant results to simple dicts
    results = []
    for hit in search_results:
        result = {
            "content": hit.payload.get("content", ""),
            "file_path": hit.payload.get("file_path", ""),
            "start_line": hit.payload.get("start_line", 0),
            "end_line": hit.payload.get("end_line", 0),
            "language": hit.payload.get("language", ""),
            "chunk_id": hit.payload.get("chunk_id", ""),
            "score": hit.score,  # Cosine similarity score (0 to 1)
        }
        results.append(result)

    logger.info(
        f"Search for repo '{repo_id}': found {len(results)} results "
        f"(top score: {results[0]['score']:.3f})" if results else
        f"Search for repo '{repo_id}': no results found"
    )
    return results


def delete_repo_vectors(repo_id: str) -> bool:
    """
    Delete all vectors belonging to a specific repository.

    Used when a user deletes a repository from the system.

    Args:
        repo_id: The repository to delete vectors for

    Returns:
        True if deletion was successful
    """
    try:
        client = get_qdrant_client()

        client.delete(
            collection_name=settings.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="repo_id",
                        match=MatchValue(value=repo_id),
                    )
                ]
            ),
        )
        logger.info(f"Deleted all vectors for repo: {repo_id}")
        return True

    except Exception as error:
        logger.error(f"Failed to delete vectors for {repo_id}: {error}")
        return False


def get_collection_info() -> dict:
    """Get information about the code_chunks collection."""
    try:
        client = get_qdrant_client()
        info = client.get_collection(settings.collection_name)
        return {
            "name": settings.collection_name,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
        }
    except Exception as error:
        logger.error(f"Failed to get collection info: {error}")
        return {"name": settings.collection_name, "error": str(error)}


def check_repo_exists(repo_id: str) -> bool:
    """
    Check if a repository has any vectors stored in Qdrant.
    """
    try:
        client = get_qdrant_client()
        result = client.count(
            collection_name=settings.collection_name,
            count_filter=Filter(
                must=[
                    FieldCondition(
                        key="repo_id",
                        match=MatchValue(value=repo_id),
                    )
                ]
            ),
            exact=True,
        )
        return result.count > 0
    except Exception as error:
        logger.error(f"Error checking if repo exists in Qdrant: {error}")
        return False


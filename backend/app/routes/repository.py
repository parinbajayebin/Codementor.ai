"""
repository.py - API routes for repository ingestion

Endpoints:
    POST /api/repository/ingest    - Submit a GitHub URL for processing
    GET  /api/repository/{id}/status - Check ingestion status
    GET  /api/repository/list      - List all ingested repos
    DELETE /api/repository/{id}    - Delete a repo and its data
    POST /api/repository/search    - Search for code chunks (Phase 2)
"""

from fastapi import APIRouter, HTTPException

from app.models.requests import IngestRepositoryRequest
from app.models.responses import (
    IngestResponse,
    StatusResponse,
    ErrorResponse,
)
from app.services import (
    github_service,
    parser_service,
    chunking_service,
    embedding_service,
    vector_service,
    retrieval_service,
)
from app.utils.cache import cache
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Create a router with the /api/repository prefix
router = APIRouter(prefix="/api/repository", tags=["Repository"])


@router.post(
    "/ingest",
    response_model=IngestResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def ingest_repository(request: IngestRepositoryRequest):
    """
    Ingest a GitHub repository for analysis.

    Full pipeline:
    1. Clone the repository (shallow clone)
    2. Scan and parse all supported source files
    3. Split files into overlapping chunks
    4. Generate embeddings for all chunks
    5. Store vectors + metadata in Qdrant
    6. Clean up cloned files
    """
    github_url = request.github_url
    logger.info(f"Ingestion request received for: {github_url}")

    # Step 1: Generate repo ID
    repo_id = github_service.generate_repo_id(github_url)
    owner, repo_name = github_service.get_repo_owner_and_name(github_url)

    # Update status in cache
    cache.set(f"repo:status:{repo_id}", {
        "repo_id": repo_id,
        "repo_name": repo_name,
        "owner": owner,
        "github_url": github_url,
        "status": "processing",
        "total_files": 0,
        "total_chunks": 0,
        "message": "Cloning repository...",
    }, ttl_seconds=3600)

    try:
        # Step 2: Clone the repository
        clone_path = github_service.clone_repository(github_url)

        # Step 3: Scan and parse files
        cache.set(f"repo:status:{repo_id}", {
            "repo_id": repo_id, "repo_name": repo_name, "owner": owner,
            "github_url": github_url, "status": "processing",
            "total_files": 0, "total_chunks": 0,
            "message": "Scanning files...",
        }, ttl_seconds=3600)

        parsed_files, skipped_reasons = parser_service.scan_repository(clone_path)

        # Step 4: Chunk the parsed files
        cache.set(f"repo:status:{repo_id}", {
            "repo_id": repo_id, "repo_name": repo_name, "owner": owner,
            "github_url": github_url, "status": "processing",
            "total_files": len(parsed_files), "total_chunks": 0,
            "message": f"Chunking {len(parsed_files)} files...",
        }, ttl_seconds=3600)

        chunks = chunking_service.chunk_parsed_files(parsed_files, repo_id)

        # Step 5: Generate embeddings
        cache.set(f"repo:status:{repo_id}", {
            "repo_id": repo_id, "repo_name": repo_name, "owner": owner,
            "github_url": github_url, "status": "processing",
            "total_files": len(parsed_files), "total_chunks": len(chunks),
            "message": f"Generating embeddings for {len(chunks)} chunks...",
        }, ttl_seconds=3600)

        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = embedding_service.generate_embeddings_batch(chunk_texts)

        # Step 6: Store vectors in Qdrant
        cache.set(f"repo:status:{repo_id}", {
            "repo_id": repo_id, "repo_name": repo_name, "owner": owner,
            "github_url": github_url, "status": "processing",
            "total_files": len(parsed_files), "total_chunks": len(chunks),
            "message": f"Storing {len(chunks)} vectors in Qdrant...",
        }, ttl_seconds=3600)

        stored_count = vector_service.store_vectors(chunks, embeddings)

        # Step 7: Clean up cloned repo
        github_service.cleanup_repository(repo_id)

        # Cache file list
        file_list = [f.to_dict() for f in parsed_files]
        cache.set(f"repo:files:{repo_id}", file_list, ttl_seconds=1800)

        # Update status to completed
        cache.set(f"repo:status:{repo_id}", {
            "repo_id": repo_id,
            "repo_name": repo_name,
            "owner": owner,
            "github_url": github_url,
            "status": "completed",
            "total_files": len(parsed_files),
            "total_chunks": stored_count,
            "message": f"Successfully ingested {len(parsed_files)} files "
                       f"into {stored_count} searchable chunks.",
        }, ttl_seconds=86400)  # 24 hour TTL for completed repos

        logger.info(
            f"Ingestion complete for {repo_id}: "
            f"{len(parsed_files)} files -> {stored_count} chunks"
        )

        return IngestResponse(
            message=f"Repository ingested successfully. "
                    f"{len(parsed_files)} files → {stored_count} chunks.",
            repo_id=repo_id,
            status="completed",
        )

    except Exception as error:
        # Update status to failed
        cache.set(f"repo:status:{repo_id}", {
            "repo_id": repo_id, "repo_name": repo_name, "owner": owner,
            "github_url": github_url, "status": "failed",
            "total_files": 0, "total_chunks": 0,
            "message": str(error),
        }, ttl_seconds=300)

        # Clean up if clone partially succeeded
        github_service.cleanup_repository(repo_id)

        logger.error(f"Ingestion failed for {repo_id}: {error}")
        raise HTTPException(status_code=500, detail=str(error))


@router.get(
    "/{repo_id}/status",
    response_model=StatusResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_repository_status(repo_id: str):
    """Check the ingestion status of a repository."""
    cached_status = cache.get(f"repo:status:{repo_id}")

    if cached_status is None:
        raise HTTPException(
            status_code=404,
            detail=f"No repository found with ID: {repo_id}. "
                   f"Submit a GitHub URL first via POST /api/repository/ingest",
        )

    return StatusResponse(
        repo_id=cached_status["repo_id"],
        status=cached_status["status"],
        total_files=cached_status.get("total_files", 0),
        total_chunks=cached_status.get("total_chunks", 0),
        message=cached_status.get("message", ""),
    )


@router.get("/list")
def list_repositories():
    """List all ingested repositories from Redis cache."""
    if not cache.is_connected:
        return {"repositories": [], "message": "Cache unavailable"}

    try:
        keys = cache.client.keys("repo:status:*")
        repositories = []
        for key in keys:
            data = cache.get(key)
            if data and data.get("status") == "completed":
                repositories.append(data)
        return {"repositories": repositories}
    except Exception as error:
        logger.error(f"Error listing repositories: {error}")
        return {"repositories": [], "message": str(error)}


@router.post("/search")
def search_repository_chunks(repo_id: str, question: str):
    """
    Search for relevant code chunks in a repository.

    This is a standalone search endpoint for testing retrieval
    quality before the full RAG pipeline is wired up.
    """
    results = retrieval_service.search_repository(question, repo_id)

    return {
        "repo_id": repo_id,
        "question": question,
        "results_count": len(results),
        "results": results,
    }


@router.delete(
    "/{repo_id}",
    responses={404: {"model": ErrorResponse}},
)
def delete_repository(repo_id: str):
    """Delete a repository, its cached data, and its vectors from Qdrant."""
    cached_status = cache.get(f"repo:status:{repo_id}")
    if cached_status is None:
        raise HTTPException(
            status_code=404,
            detail=f"No repository found with ID: {repo_id}",
        )

    # Delete vectors from Qdrant
    try:
        vector_service.delete_repo_vectors(repo_id)
    except Exception as error:
        logger.warning(f"Could not delete vectors (Qdrant may be unavailable): {error}")

    # Delete all cache keys for this repo
    cache.delete(f"repo:status:{repo_id}")
    cache.delete(f"repo:files:{repo_id}")
    cache.delete_pattern(f"chat:{repo_id}:*")
    cache.delete_pattern(f"search:{repo_id}:*")

    # Clean up any leftover clone
    github_service.cleanup_repository(repo_id)

    logger.info(f"Repository deleted: {repo_id}")
    return {"message": f"Repository {repo_id} deleted successfully"}

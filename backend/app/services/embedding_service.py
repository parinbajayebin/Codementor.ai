"""
embedding_service.py - Generate vector embeddings from text

Uses the BAAI/bge-small-en-v1.5 model from HuggingFace to convert
text chunks into 384-dimensional vectors. The model runs locally
on CPU — no API calls, no cost.

The model is loaded once on first use and cached for the app lifetime.
"""

from typing import Optional

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Module-level variable to hold the loaded model
# This acts as a singleton — loaded once, reused forever
_model = None


def load_embedding_model():
    """
    Load the embedding model into memory.

    Called once on first use. The model is ~130MB and takes
    a few seconds to download on first run.

    Returns:
        The loaded SentenceTransformer model
    """
    global _model

    if _model is not None:
        return _model

    logger.info(f"Loading embedding model: {settings.embedding_model}")
    logger.info("This may take a moment on first run (downloading ~130MB)...")

    try:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(
            settings.embedding_model,
            token=settings.hf_token if settings.hf_token else None,
        )
        logger.info("Embedding model loaded successfully")
        return _model

    except Exception as error:
        logger.error(f"Failed to load embedding model: {error}")
        raise Exception(
            f"Could not load embedding model '{settings.embedding_model}'. "
            f"Make sure sentence-transformers is installed. Error: {error}"
        )


def generate_embedding(text: str) -> list[float]:
    """
    Convert a single text string into a vector embedding.

    Used for embedding user questions during query time.

    Args:
        text: The text to embed (a question, a code chunk, etc.)

    Returns:
        A list of 384 float values (the embedding vector)
    """
    model = load_embedding_model()

    # bge-small works better with a prefix for queries
    # But for simplicity, we skip the prefix (works fine without it)
    embedding = model.encode(text, show_progress_bar=False)

    # Convert numpy array to plain Python list
    return embedding.tolist()


def generate_embeddings_batch(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    """
    Convert a list of text strings into embedding vectors.

    Processes in batches for efficiency. Used during repository
    ingestion to embed all code chunks at once.

    Args:
        texts: List of text strings to embed
        batch_size: How many texts to process at once (default 32)

    Returns:
        List of embedding vectors (each is a list of 384 floats)
    """
    if not texts:
        return []

    model = load_embedding_model()

    logger.info(f"Generating embeddings for {len(texts)} texts (batch_size={batch_size})")

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
    )

    # Convert numpy arrays to plain Python lists
    result = [embedding.tolist() for embedding in embeddings]

    logger.info(f"Generated {len(result)} embeddings (dim={len(result[0])})")
    return result

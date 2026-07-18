"""
chunking_service.py - Split source code into smaller chunks

This service takes parsed files and splits them into chunks
suitable for embedding. Each chunk carries metadata so we can
trace it back to the exact file and line numbers.

Chunking Strategy:
    - Fixed-size chunks (~500 tokens ≈ 2000 characters)
    - Overlap of ~50 tokens (200 characters) to avoid losing context at boundaries
    - Each chunk stores: file_path, start_line, end_line, language, repo_id
"""

from dataclasses import dataclass

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CodeChunk:
    """
    A single chunk of source code with metadata.

    Attributes:
        chunk_id: Unique identifier for this chunk
        repo_id: Which repository this chunk belongs to
        file_path: Relative path within the repo (e.g., "src/auth/login.py")
        content: The actual text content of the chunk
        start_line: First line number in the original file
        end_line: Last line number in the original file
        language: Programming language of the file
        chunk_index: Position of this chunk within the file (0, 1, 2, ...)
    """
    chunk_id: str
    repo_id: str
    file_path: str
    content: str
    start_line: int
    end_line: int
    language: str
    chunk_index: int

    def to_payload(self) -> dict:
        """Convert to a dictionary for storing as Qdrant payload."""
        return {
            "chunk_id": self.chunk_id,
            "repo_id": self.repo_id,
            "file_path": self.file_path,
            "content": self.content,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "language": self.language,
            "chunk_index": self.chunk_index,
        }


def split_text_into_chunks(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> list[tuple[str, int, int]]:
    """
    Split text into overlapping chunks based on character count.

    Returns a list of (chunk_text, start_line, end_line) tuples.
    Line numbers are 1-indexed to match how code editors show them.

    Args:
        text: The full text content to split
        chunk_size: Max characters per chunk (default from settings)
        chunk_overlap: Overlap characters between chunks (default from settings)

    Returns:
        List of (chunk_text, start_line, end_line) tuples
    """
    if chunk_size is None:
        chunk_size = settings.chunk_size
    if chunk_overlap is None:
        chunk_overlap = settings.chunk_overlap

    lines = text.split("\n")
    total_lines = len(lines)

    if total_lines == 0:
        return []

    chunks = []
    current_start_line = 0  # 0-indexed internally

    while current_start_line < total_lines:
        # Build chunk by adding lines until we hit the size limit
        current_chunk_lines = []
        current_char_count = 0
        current_end_line = current_start_line

        for i in range(current_start_line, total_lines):
            line = lines[i]
            line_length = len(line) + 1  # +1 for the newline character

            # If adding this line would exceed chunk_size and we already have content
            if current_char_count + line_length > chunk_size and current_chunk_lines:
                break

            current_chunk_lines.append(line)
            current_char_count += line_length
            current_end_line = i

        # Create the chunk text
        chunk_text = "\n".join(current_chunk_lines).strip()

        if chunk_text:  # Don't add empty chunks
            chunks.append((
                chunk_text,
                current_start_line + 1,  # Convert to 1-indexed
                current_end_line + 1,     # Convert to 1-indexed
            ))

        # Move to next chunk position, stepping back by overlap
        # Calculate how many lines to step back for overlap
        overlap_chars = 0
        overlap_lines = 0
        for i in range(current_end_line, current_start_line, -1):
            overlap_chars += len(lines[i]) + 1
            overlap_lines += 1
            if overlap_chars >= chunk_overlap:
                break

        next_start = current_end_line + 1 - overlap_lines

        # Safety: always move forward by at least 1 line
        if next_start <= current_start_line:
            next_start = current_end_line + 1

        current_start_line = next_start

    return chunks


def chunk_parsed_files(
    parsed_files: list,
    repo_id: str,
) -> list[CodeChunk]:
    """
    Take a list of parsed files and split them all into chunks.

    This is the main entry point for the chunking service.

    Args:
        parsed_files: List of ParsedFile objects from parser_service
        repo_id: The repository identifier

    Returns:
        List of CodeChunk objects ready for embedding
    """
    all_chunks = []
    chunk_counter = 0

    for parsed_file in parsed_files:
        # Split this file into chunks
        text_chunks = split_text_into_chunks(parsed_file.content)

        for chunk_index, (chunk_text, start_line, end_line) in enumerate(text_chunks):
            chunk_id = f"{repo_id}:{parsed_file.file_path}:{chunk_counter}"

            code_chunk = CodeChunk(
                chunk_id=chunk_id,
                repo_id=repo_id,
                file_path=parsed_file.file_path,
                content=chunk_text,
                start_line=start_line,
                end_line=end_line,
                language=parsed_file.language,
                chunk_index=chunk_index,
            )
            all_chunks.append(code_chunk)
            chunk_counter += 1

    logger.info(
        f"Chunking complete for {repo_id}: "
        f"{len(parsed_files)} files -> {len(all_chunks)} chunks"
    )
    return all_chunks

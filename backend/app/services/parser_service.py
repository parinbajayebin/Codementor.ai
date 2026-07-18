"""
parser_service.py - Parse and scan repository files

This service handles:
1. Walking through a cloned repo's file tree
2. Filtering files by extension, size, and directory
3. Reading file contents safely (skip binary files)
4. Returning a list of parsed files with metadata
"""

import os
from typing import Optional

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


# File extensions we know how to process
SUPPORTED_EXTENSIONS: set[str] = {
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".java", ".go", ".rs",
    ".md", ".txt",
    ".yaml", ".yml", ".json",
    ".html", ".css",
    ".c", ".cpp", ".h",
    ".rb", ".php",
    ".sh", ".bash",
    ".sql",
    ".toml", ".cfg", ".ini",
    ".xml",
    ".dockerfile",
}

# Directories to always skip
IGNORED_DIRECTORIES: set[str] = {
    "node_modules", ".git", "__pycache__", "dist", "build",
    ".venv", "venv", "env", ".next", "target", "vendor",
    ".idea", ".vscode", "coverage", ".nyc_output",
    ".tox", ".mypy_cache", ".pytest_cache",
    "egg-info", ".eggs",
}

# Files to always skip (lock files, large generated files)
IGNORED_FILES: set[str] = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "poetry.lock", "Pipfile.lock", "composer.lock",
    "Gemfile.lock", "Cargo.lock",
}


class ParsedFile:
    """
    Represents a single parsed source file.

    Attributes:
        file_path: Path relative to repo root (e.g., "src/auth/login.py")
        content: The text content of the file
        language: Programming language (e.g., "python")
        size_bytes: File size in bytes
    """

    def __init__(self, file_path: str, content: str, language: str, size_bytes: int):
        self.file_path = file_path
        self.content = content
        self.language = language
        self.size_bytes = size_bytes

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_path": self.file_path,
            "language": self.language,
            "size_bytes": self.size_bytes,
        }


def get_language_from_extension(extension: str) -> str:
    """
    Map a file extension to a human-readable language name.

    Args:
        extension: File extension like ".py"

    Returns:
        Language name like "python"
    """
    extension_to_language = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".md": "markdown",
        ".txt": "text",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
        ".html": "html",
        ".css": "css",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".rb": "ruby",
        ".php": "php",
        ".sh": "shell",
        ".bash": "shell",
        ".sql": "sql",
        ".toml": "toml",
        ".cfg": "config",
        ".ini": "config",
        ".xml": "xml",
        ".dockerfile": "dockerfile",
    }
    return extension_to_language.get(extension, "unknown")


def should_skip_directory(directory_name: str) -> bool:
    """Check if a directory should be skipped during scanning."""
    return directory_name.lower() in IGNORED_DIRECTORIES


def should_skip_file(file_name: str, file_size: int) -> tuple[bool, Optional[str]]:
    """
    Check if a file should be skipped.

    Returns:
        Tuple of (should_skip, reason_why)
    """
    # Check ignored file names
    if file_name in IGNORED_FILES:
        return True, f"Ignored file: {file_name}"

    # Check file extension
    _, extension = os.path.splitext(file_name)
    extension = extension.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        # Special case: Dockerfile (no extension)
        if file_name.lower() == "dockerfile":
            return False, None
        return True, f"Unsupported extension: {extension or 'none'}"

    # Check file size
    if file_size > settings.max_file_size:
        return True, f"File too large: {file_size} bytes (max: {settings.max_file_size})"

    return False, None


def read_file_safely(file_path: str) -> Optional[str]:
    """
    Read a file as UTF-8 text. Returns None if the file is binary or unreadable.

    Args:
        file_path: Absolute path to the file

    Returns:
        File content as string, or None if unreadable
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="strict") as file:
            return file.read()
    except (UnicodeDecodeError, PermissionError, OSError):
        return None


def scan_repository(repo_path: str) -> tuple[list[ParsedFile], list[str]]:
    """
    Walk through a cloned repository and parse all supported files.

    This is the main function of the parser service. It:
    1. Walks the file tree recursively
    2. Skips ignored directories and files
    3. Reads supported files as UTF-8
    4. Returns parsed files and a list of skip reasons

    Args:
        repo_path: Absolute path to the cloned repository

    Returns:
        Tuple of (list of ParsedFile objects, list of skip reasons)
    """
    parsed_files: list[ParsedFile] = []
    skipped_reasons: list[str] = []
    files_processed = 0

    logger.info(f"Scanning repository at: {repo_path}")

    for root, directories, files in os.walk(repo_path):
        # Filter out ignored directories (modifying in-place skips them)
        directories[:] = [
            d for d in directories
            if not should_skip_directory(d)
        ]

        for file_name in files:
            # Stop if we hit the file limit
            if files_processed >= settings.max_files_per_repo:
                skipped_reasons.append(
                    f"File limit reached ({settings.max_files_per_repo}). "
                    f"Remaining files skipped."
                )
                logger.warning(f"File limit reached at {files_processed} files")
                return parsed_files, skipped_reasons

            absolute_path = os.path.join(root, file_name)
            file_size = os.path.getsize(absolute_path)

            # Check if file should be skipped
            should_skip, reason = should_skip_file(file_name, file_size)
            if should_skip:
                skipped_reasons.append(f"{file_name}: {reason}")
                continue

            # Try to read the file
            content = read_file_safely(absolute_path)
            if content is None:
                skipped_reasons.append(f"{file_name}: Binary or unreadable file")
                continue

            # Skip empty files
            if not content.strip():
                skipped_reasons.append(f"{file_name}: Empty file")
                continue

            # Get the relative path (e.g., "src/auth/login.py")
            relative_path = os.path.relpath(absolute_path, repo_path)
            # Normalize to forward slashes for consistency
            relative_path = relative_path.replace("\\", "/")

            # Determine language
            _, extension = os.path.splitext(file_name)
            language = get_language_from_extension(extension.lower())

            # Handle Dockerfile special case
            if file_name.lower() == "dockerfile":
                language = "dockerfile"

            parsed_file = ParsedFile(
                file_path=relative_path,
                content=content,
                language=language,
                size_bytes=file_size,
            )
            parsed_files.append(parsed_file)
            files_processed += 1

    logger.info(
        f"Scan complete: {len(parsed_files)} files parsed, "
        f"{len(skipped_reasons)} files skipped"
    )
    return parsed_files, skipped_reasons

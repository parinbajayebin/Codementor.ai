"""
github_service.py - Clone and manage GitHub repositories

This service handles:
1. Cloning a GitHub repo to a temp directory
2. Generating a unique repo_id from the URL
3. Cleaning up cloned repos after processing
"""

import os
import shutil

from git import Repo, GitCommandError

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def generate_repo_id(github_url: str) -> str:
    """
    Create a unique repo_id from a GitHub URL.

    Example:
        "https://github.com/fastapi/fastapi" -> "fastapi-fastapi"

    Args:
        github_url: Full GitHub repository URL

    Returns:
        A string like "owner-reponame"
    """
    # Remove https://github.com/ and any trailing slashes or .git
    path = github_url.replace("https://github.com/", "").strip("/")
    if path.endswith(".git"):
        path = path[:-4]

    # Replace / with - to make a flat ID
    repo_id = path.replace("/", "-").lower()
    return repo_id


def get_repo_owner_and_name(github_url: str) -> tuple[str, str]:
    """
    Extract owner and repo name from GitHub URL.

    Example:
        "https://github.com/fastapi/fastapi" -> ("fastapi", "fastapi")

    Args:
        github_url: Full GitHub repository URL

    Returns:
        Tuple of (owner, repo_name)
    """
    path = github_url.replace("https://github.com/", "").strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    parts = path.split("/")
    return parts[0], parts[1]


def clone_repository(github_url: str) -> str:
    """
    Clone a GitHub repository to a local directory.

    The repo is cloned into: cloned_repos/{repo_id}/

    Args:
        github_url: The GitHub URL to clone

    Returns:
        The local path where the repo was cloned

    Raises:
        Exception: If cloning fails (bad URL, private repo, network error)
    """
    repo_id = generate_repo_id(github_url)
    clone_path = os.path.join(settings.clone_directory, repo_id)

    # If already cloned, remove and re-clone (fresh copy)
    if os.path.exists(clone_path):
        logger.info(f"Removing existing clone: {clone_path}")
        shutil.rmtree(clone_path)

    logger.info(f"Cloning {github_url} into {clone_path}")

    try:
        Repo.clone_from(
            url=github_url,
            to_path=clone_path,
            depth=1,  # Shallow clone - only latest commit (faster, less disk)
        )
        logger.info(f"Clone successful: {clone_path}")
        return clone_path

    except GitCommandError as error:
        logger.error(f"Git clone failed for {github_url}: {error}")
        raise Exception(
            f"Failed to clone repository. Make sure the URL is correct "
            f"and the repository is public. Error: {error}"
        )


def force_remove_readonly(func, path, exc_info):
    """
    Error handler for shutil.rmtree on Windows.
    Git pack files are often read-only. This forces them writable first.
    """
    import stat
    os.chmod(path, stat.S_IWRITE)
    func(path)


def cleanup_repository(repo_id: str) -> bool:
    """
    Delete a cloned repository from disk.

    Called after ingestion is complete to save disk space.

    Args:
        repo_id: The repository ID (e.g., "fastapi-fastapi")

    Returns:
        True if cleanup was successful
    """
    clone_path = os.path.join(settings.clone_directory, repo_id)

    if os.path.exists(clone_path):
        shutil.rmtree(clone_path, onexc=force_remove_readonly)
        logger.info(f"Cleaned up cloned repo: {clone_path}")
        return True

    logger.info(f"No clone found to clean up: {clone_path}")
    return False

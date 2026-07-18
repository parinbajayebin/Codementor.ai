"""
requests.py - Pydantic models for incoming API requests

Every request body is validated through these models.
If validation fails, FastAPI returns a 422 error automatically.
"""

from pydantic import BaseModel, field_validator


class IngestRepositoryRequest(BaseModel):
    """
    Request body for POST /api/repository/ingest

    Example:
        {"github_url": "https://github.com/user/repo"}
    """
    github_url: str

    @field_validator("github_url")
    @classmethod
    def validate_github_url(cls, url: str) -> str:
        """Make sure the URL looks like a valid GitHub repository."""
        url = url.strip()

        # Must start with https://github.com/
        if not url.startswith("https://github.com/"):
            raise ValueError(
                "URL must start with https://github.com/. "
                "Example: https://github.com/user/repo"
            )

        # Must have at least user/repo after github.com
        path_parts = url.replace("https://github.com/", "").strip("/").split("/")
        if len(path_parts) < 2 or not path_parts[0] or not path_parts[1]:
            raise ValueError(
                "URL must include owner and repo name. "
                "Example: https://github.com/user/repo"
            )

        # Remove .git suffix if present
        if url.endswith(".git"):
            url = url[:-4]

        return url


class AskQuestionRequest(BaseModel):
    """
    Request body for POST /api/chat/ask

    Example:
        {"repo_id": "user-repo", "question": "How does auth work?"}
    """
    repo_id: str
    question: str

    @field_validator("question")
    @classmethod
    def question_must_not_be_empty(cls, question: str) -> str:
        """Make sure the question is not empty."""
        if not question.strip():
            raise ValueError("Question cannot be empty.")
        return question.strip()

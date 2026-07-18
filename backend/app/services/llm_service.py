"""
llm_service.py - Interact with LLMs via OpenRouter API

Sends prompts to Qwen or other LLMs on OpenRouter. Builds the system prompt
and injects retrieved code context to run the RAG loop.
"""

import httpx
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def generate_answer(
    question: str,
    context: str,
    chat_history: list[dict] = None,
) -> str:
    """
    Send the question and retrieved code context to the LLM.

    Args:
        question: The user's query
        context: Formatted code context from retrieval_service
        chat_history: Optional list of previous chat messages to provide context

    Returns:
        The generated answer text
    """
    if not settings.openrouter_api_key:
        raise Exception(
            "OpenRouter API key not configured. "
            "Set OPENROUTER_API_KEY in your .env file."
        )

    # Build system prompt instructing LLM to behave as a Code Mentor
    system_prompt = (
        "You are CodeMentor AI, an expert software architect and mentor.\n"
        "Your task is to help the user understand a codebase by answering their questions "
        "using the provided source code context.\n\n"
        "Guidelines:\n"
        "1. Strictly use the provided source code snippets to construct your answer.\n"
        "2. Cite your sources using '[Source N]' format (e.g., [Source 1], [Source 2]) "
        "inline when referencing parts of the codebase.\n"
        "3. If the answer cannot be determined from the provided context, state that you "
        "cannot find the answer in the provided source files. Do not make things up.\n"
        "4. Keep explanations clear, professional, and educational. Use markdown formatting "
        "and code blocks for readability.\n"
    )

    messages = [{"role": "system", "content": system_prompt}]

    # Add historical messages if present to allow conversation flow
    if chat_history:
        for msg in chat_history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })

    # Prepare user query with the code context
    user_content = (
        f"Here is the relevant code context retrieved from the repository:\n\n"
        f"{context}\n\n"
        f"Question: {question}\n"
        f"Answer:"
    )
    messages.append({"role": "user", "content": user_content})

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "CodeMentor AI",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.llm_model,
        "messages": messages,
        "temperature": 0.2,  # Low temperature for factual code answers
    }

    logger.info(f"Sending prompt to OpenRouter LLM: {settings.llm_model}")

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
            )

            if response.status_code != 200:
                logger.error(f"OpenRouter API error: Status {response.status_code} - {response.text}")
                raise Exception(f"OpenRouter API returned error status: {response.status_code}")

            res_json = response.json()
            choices = res_json.get("choices", [])
            if not choices:
                logger.error("No choices returned from OpenRouter API")
                raise Exception("Empty response from LLM")

            answer = choices[0].get("message", {}).get("content", "").strip()
            logger.info("Answer generated successfully from LLM")
            return answer

    except Exception as error:
        logger.error(f"Failed to communicate with LLM: {error}")
        raise Exception(f"Failed to generate answer from LLM: {error}")

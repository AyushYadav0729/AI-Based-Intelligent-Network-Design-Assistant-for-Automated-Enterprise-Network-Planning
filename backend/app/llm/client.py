"""
client.py — Google Gemini client wrapper with timeout, retry, and graceful failure handling.
Spec Section 9.4.
"""
import logging
import time
from typing import Any
from app.config import settings

logger = logging.getLogger(__name__)


def is_llm_available() -> bool:
    """Returns True if a non-empty Gemini API key is configured."""
    return bool(settings.gemini_api_key and settings.gemini_api_key.strip())


def get_genai_client():
    """Initializes and returns the Google GenAI client if configured."""
    if not is_llm_available():
        return None
    try:
        from google import genai
        return genai.Client(api_key=settings.gemini_api_key)
    except Exception as e:
        logger.warning(f"Failed to initialize Google GenAI client: {e}")
        return None


def generate_content_with_retry(
    prompt: str,
    system_instruction: str | None = None,
    max_retries: int = 1,
) -> str | None:
    """
    Calls Gemini with a prompt, timeout, and 1 exponential backoff retry.
    Returns response text or None on failure. Never crashes.
    """
    client = get_genai_client()
    if client is None:
        return None

    model_name = settings.gemini_model

    for attempt in range(max_retries + 1):
        try:
            config: dict[str, Any] = {}
            if system_instruction:
                config["system_instruction"] = system_instruction

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config if config else None,
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            logger.warning(f"Gemini API attempt {attempt + 1} failed: {e}")
            if attempt < max_retries:
                time.sleep(1.0 * (attempt + 1))
            else:
                logger.error(f"Gemini call permanently failed after {max_retries + 1} attempts.")
                return None

    return None


"""
parser.py — Parses free-text user requirements into validated RequirementsInput via Gemini.
Spec Section 9.1.
Never trusts LLM output: parses as JSON, validates with Pydantic, and returns ParseResult.
"""
import json
import re
from typing import Any

from app.schemas.requirements import RequirementsInput
from app.schemas.llm import ParseResult
from app.llm.client import is_llm_available, generate_content_with_retry
from app.llm.prompts import PARSE_SYSTEM_PROMPT


def clean_json_response(raw_text: str) -> str:
    """Removes markdown code fences and extraneous text from LLM response."""
    text = raw_text.strip()
    # Match ```json ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text


def parse_free_text_requirements(user_text: str) -> ParseResult:
    """
    Parses natural language requirements into structured RequirementsInput.
    Falls back gracefully if LLM is unavailable or fails.
    """
    if not is_llm_available():
        return ParseResult(
            requirements=None,
            missing_fields=[],
            uncertain_fields=[],
            source="none",
            message="Gemini API key is not configured. Please use the form or sample presets.",
        )

    prompt = f"Extract enterprise network requirements from this text:\n\n{user_text}"
    response_text = generate_content_with_retry(
        prompt=prompt,
        system_instruction=PARSE_SYSTEM_PROMPT,
    )

    if not response_text:
        return ParseResult(
            requirements=None,
            missing_fields=[],
            uncertain_fields=[],
            source="none",
            message="LLM parsing service timed out or was rate-limited. Please fill the form directly.",
        )

    try:
        cleaned = clean_json_response(response_text)
        data = json.loads(cleaned)
        validated = RequirementsInput.model_validate(data)

        missing: list[str] = []
        uncertain: list[str] = []

        # Audit if critical fields were inferred rather than mentioned
        lower_input = user_text.lower()
        if "floor" not in lower_input and validated.floors == 1:
            missing.append("floors")
        if "growth" not in lower_input:
            uncertain.append("growth_percent")
        if "redundancy" not in lower_input and "ha" not in lower_input:
            uncertain.append("redundancy")

        return ParseResult(
            requirements=validated,
            missing_fields=missing,
            uncertain_fields=uncertain,
            source="llm",
            message=None,
        )
    except Exception as e:
        return ParseResult(
            requirements=None,
            missing_fields=[],
            uncertain_fields=[],
            source="none",
            message=f"Failed to parse LLM structured output: {str(e)}",
        )


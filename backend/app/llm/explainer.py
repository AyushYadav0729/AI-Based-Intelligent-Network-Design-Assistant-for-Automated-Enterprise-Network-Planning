"""
explainer.py — Natural language explanation generator for architectural decisions.
Spec Section 9.2, 9.3, and 9.4.
Enforces numeric sanity guard, caching, and deterministic Jinja2 template fallbacks.
"""
import hashlib
import json
import re
from typing import Any

from app.schemas.design import Decision
from app.llm.client import is_llm_available, generate_content_with_retry
from app.llm.prompts import EXPLAIN_SYSTEM_PROMPT
from app.llm.fallback_templates import render_template_explanation

# Memory cache for explanations keyed by decision hash
_EXPLANATION_CACHE: dict[str, dict[str, str]] = {}

# Standard small integers that are safe to appear in prose (e.g. "top 2 switches", "0-indexed")
SAFE_NUMBERS = {"0", "1", "2", "3", "4", "5", "10", "20", "24", "48", "100"}


def _compute_decisions_hash(decisions: list[Decision]) -> str:
    """Computes a SHA-256 hash of the decision parameters for caching."""
    data = [
        {"code": d.reason_code, "choice": d.choice, "params": d.params}
        for d in decisions
    ]
    raw = json.dumps(data, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _extract_numbers(text: str) -> set[str]:
    """Extracts all integer and floating point numbers from a text string."""
    # Strip commas in numbers like 1,000 -> 1000
    cleaned = re.sub(r"(?<=\d),(?=\d)", "", text)
    return set(re.findall(r"\b\d+(?:\.\d+)?\b", cleaned))


def _extract_param_numbers(params: dict[str, Any]) -> set[str]:
    """Recursively extracts all numeric values present in a decision's parameter dictionary."""
    numbers: set[str] = set()

    def _walk(obj: Any):
        if isinstance(obj, (int, float)):
            # Add both int and float representations
            numbers.add(str(obj))
            if isinstance(obj, float) and obj.is_integer():
                numbers.add(str(int(obj)))
        elif isinstance(obj, str):
            numbers.update(_extract_numbers(obj))
        elif isinstance(obj, dict):
            for v in obj.values():
                _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)

    _walk(params)
    return numbers


def verify_numeric_sanity(explanation: str, params: dict[str, Any]) -> bool:
    """
    Sanity guard: Checks that numbers in the explanation exist in decision params.
    Spec Section 9.2: Discards hallucinated numbers.
    """
    exp_numbers = _extract_numbers(explanation)
    param_numbers = _extract_param_numbers(params)
    allowed = param_numbers | SAFE_NUMBERS

    for num in exp_numbers:
        # Also check if int version of float matches (e.g. 50.0 vs 50)
        try:
            num_float = float(num)
            num_int_str = str(int(num_float))
            if num in allowed or num_int_str in allowed:
                continue
        except ValueError:
            pass

        if num not in allowed:
            # Found a hallucinated number
            return False

    return True


def explain_decisions(
    decisions: list[Decision],
) -> tuple[list[Decision], str]:
    """
    Enriches Decision objects with natural language explanations.
    Uses Gemini when available; applies sanity guard; falls back to Jinja2 templates.
    Returns (enriched_decisions, explanation_source).
    """
    cache_key = _compute_decisions_hash(decisions)
    cached_explanations = _EXPLANATION_CACHE.get(cache_key)

    # 1. Try Gemini if available and not cached
    llm_explanations: dict[str, str] = {}
    source = "template"

    if cached_explanations:
        llm_explanations = cached_explanations
        source = "llm"
    elif is_llm_available():
        decision_payload = [
            {
                "reason_code": d.reason_code,
                "stage": d.stage,
                "choice": d.choice,
                "params": d.params,
            }
            for d in decisions
        ]
        prompt = (
            "Generate concise explanations for each decision based on the exact parameters provided:\n\n"
            + json.dumps(decision_payload, indent=2)
        )
        response_text = generate_content_with_retry(
            prompt=prompt,
            system_instruction=EXPLAIN_SYSTEM_PROMPT,
        )

        if response_text:
            try:
                # Clean fences if present
                cleaned = re.sub(r"```(?:json)?\s*([\s\S]*?)\s*```", r"\1", response_text).strip()
                parsed = json.loads(cleaned)
                if isinstance(parsed, dict):
                    llm_explanations = parsed
                    _EXPLANATION_CACHE[cache_key] = parsed
                    source = "llm"
            except Exception:
                pass

    # 2. Enrich decisions applying numeric sanity guard
    enriched: list[Decision] = []
    used_any_llm = False

    for d in decisions:
        candidate_text = llm_explanations.get(d.reason_code)
        explanation = None

        if candidate_text:
            if verify_numeric_sanity(candidate_text, d.params):
                explanation = candidate_text
                used_any_llm = True

        if not explanation:
            # Fallback to Jinja2 template
            explanation = render_template_explanation(d.reason_code, d.params)

        enriched.append(
            d.model_copy(update={"explanation": explanation})
        )

    final_source = "llm" if (source == "llm" and used_any_llm) else "template"
    return enriched, final_source


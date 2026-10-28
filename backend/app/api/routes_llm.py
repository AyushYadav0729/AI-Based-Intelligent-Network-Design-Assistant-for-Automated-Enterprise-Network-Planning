"""
routes_llm.py — Endpoints for natural language processing and requirements parsing.
Spec Section 9.1 and 10.
"""
from fastapi import APIRouter
from app.schemas.llm import ParseRequest, ParseResult
from app.llm.parser import parse_free_text_requirements

router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.post("/parse", response_model=ParseResult)
def parse_requirements(payload: ParseRequest) -> ParseResult:
    """
    Parses natural language requirements into structured RequirementsInput using Gemini.
    Falls back gracefully with source='none' if Gemini is not configured or unavailable.
    """
    return parse_free_text_requirements(payload.text)


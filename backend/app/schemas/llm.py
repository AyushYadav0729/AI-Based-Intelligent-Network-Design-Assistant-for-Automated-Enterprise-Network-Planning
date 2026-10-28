"""
llm.py — Pydantic models for free-text requirement parsing and LLM responses.
Spec Section 9.1 and 10.
"""
from typing import Literal
from pydantic import BaseModel, Field
from app.schemas.requirements import RequirementsInput


class ParseRequest(BaseModel):
    text: str = Field(..., min_length=5, description="Free-text description of network requirements")


class ParseResult(BaseModel):
    requirements: RequirementsInput | None = None
    missing_fields: list[str] = Field(default_factory=list)
    uncertain_fields: list[str] = Field(default_factory=list)
    source: Literal["llm", "none"] = "llm"
    message: str | None = None


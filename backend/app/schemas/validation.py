"""
validation.py — Pydantic models for validation issues.
Spec Section 5.2 and Section 7.
"""
from typing import Literal
from pydantic import BaseModel, Field

IssueSeverity = Literal["error", "warning", "info"]


class ValidationIssue(BaseModel):
    code: str
    severity: IssueSeverity
    message: str
    related: list[str] = Field(default_factory=list)


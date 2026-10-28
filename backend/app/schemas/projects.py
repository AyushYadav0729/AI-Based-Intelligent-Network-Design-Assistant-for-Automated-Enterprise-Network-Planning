"""
projects.py — Pydantic models for project persistence and comparison.
Spec Section 10 and 11.
"""
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

from app.schemas.requirements import RequirementsInput
from app.schemas.design import DesignResult, DesignGenerateResponse
from app.schemas.validation import ValidationIssue


class ProjectCreate(BaseModel):
    name: str | None = None
    requirements: RequirementsInput
    results: DesignGenerateResponse
    explanation_source: str = "template"


class ProjectListItem(BaseModel):
    id: int
    name: str
    org_type: str
    created_at: datetime
    explanation_source: str
    balanced_cost: float | None = None
    topology: str | None = None


class ProjectDetail(BaseModel):
    id: int
    name: str
    org_type: str
    created_at: datetime
    requirements: RequirementsInput
    results: DesignGenerateResponse
    explanation_source: str


class ProjectCompareResponse(BaseModel):
    projects: list[dict[str, Any]]
    comparison_metrics: list[dict[str, Any]]


class ValidateDesignRequest(BaseModel):
    design: DesignResult
    requirements: RequirementsInput


class ValidateDesignResponse(BaseModel):
    issues: list[ValidationIssue]
    error_count: int
    warning_count: int
    info_count: int


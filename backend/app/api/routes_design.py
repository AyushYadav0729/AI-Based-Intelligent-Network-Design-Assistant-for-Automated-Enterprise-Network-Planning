"""
routes_design.py — Endpoints for network design generation, validation, and catalog queries.
Spec Section 10.
"""
from fastapi import APIRouter, HTTPException
from app.schemas.requirements import RequirementsInput
from app.schemas.design import DesignGenerateResponse
from app.schemas.catalog import DeviceCatalog
from app.schemas.projects import ValidateDesignRequest, ValidateDesignResponse
from app.catalog.loader import get_catalog
from app.engine.variants import generate_all_variants
from app.engine.validator import validate_design

router = APIRouter(prefix="/api", tags=["design"])


@router.post("/design/generate", response_model=DesignGenerateResponse)
def generate_design(requirements: RequirementsInput) -> DesignGenerateResponse:
    """
    Generates three network design variants (Budget, Balanced, High-performance)
    complete with VLSM IP plan, topology, devices, routing, security, costs, and comparison.
    """
    try:
        return generate_all_variants(requirements)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Design generation failed: {str(e)}")


@router.post("/design/validate", response_model=ValidateDesignResponse)
def validate_existing_design(payload: ValidateDesignRequest) -> ValidateDesignResponse:
    """
    Re-evaluates rule-based validation checks on a given design result and requirements.
    """
    issues = validate_design(payload.design, payload.requirements)
    errors = sum(1 for i in issues if i.severity == "error")
    warnings = sum(1 for i in issues if i.severity == "warning")
    infos = sum(1 for i in issues if i.severity == "info")

    return ValidateDesignResponse(
        issues=issues,
        error_count=errors,
        warning_count=warnings,
        info_count=infos,
    )


@router.get("/catalog", response_model=DeviceCatalog)
def get_device_catalog() -> DeviceCatalog:
    """
    Returns the loaded and validated hardware device catalog.
    """
    return get_catalog()


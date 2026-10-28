"""
routes_projects.py — Endpoints for managing and comparing saved network design projects.
Spec Section 10 and 11.
"""
import json
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import ProjectModel
from app.schemas.requirements import RequirementsInput
from app.schemas.design import DesignGenerateResponse, DesignResult
from app.schemas.projects import (
    ProjectCreate,
    ProjectListItem,
    ProjectDetail,
    ProjectCompareResponse,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectDetail, status_code=status.HTTP_201_CREATED)
def save_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> ProjectDetail:
    """Saves a project (requirements and all variant results)."""
    proj_name = payload.name or payload.requirements.org_name
    req_json = payload.requirements.model_dump_json()
    res_json = payload.results.model_dump_json()

    project = ProjectModel(
        name=proj_name,
        org_type=payload.requirements.org_type,
        requirements_json=req_json,
        results_json=res_json,
        explanation_source=payload.explanation_source,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    return ProjectDetail(
        id=project.id,
        name=project.name,
        org_type=project.org_type,
        created_at=project.created_at,
        requirements=payload.requirements,
        results=payload.results,
        explanation_source=project.explanation_source,
    )


@router.get("", response_model=list[ProjectListItem])
def list_projects(db: Session = Depends(get_db)) -> list[ProjectListItem]:
    """Lists all saved projects with summary cost and topology metadata."""
    projects = db.query(ProjectModel).order_by(ProjectModel.created_at.desc()).all()
    items: list[ProjectListItem] = []

    for p in projects:
        cost = None
        topo = None
        try:
            results_data = json.loads(p.results_json)
            balanced = results_data.get("variants", {}).get("balanced", {})
            cost = balanced.get("cost", {}).get("total_cost")
            topo = balanced.get("topology")
        except Exception:
            pass

        items.append(
            ProjectListItem(
                id=p.id,
                name=p.name,
                org_type=p.org_type,
                created_at=p.created_at,
                explanation_source=p.explanation_source,
                balanced_cost=cost,
                topology=topo,
            )
        )

    return items


@router.get("/compare", response_model=ProjectCompareResponse)
def compare_projects(
    ids: str = Query(..., description="Comma-separated project IDs, e.g. 1,2"),
    db: Session = Depends(get_db),
) -> ProjectCompareResponse:
    """Compares saved project designs side-by-side."""
    try:
        id_list = [int(i.strip()) for i in ids.split(",") if i.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID list format")

    if len(id_list) < 2:
        raise HTTPException(status_code=400, detail="At least 2 project IDs are required for comparison")

    projects = db.query(ProjectModel).filter(ProjectModel.id.in_(id_list)).all()
    if len(projects) != len(id_list):
        found_ids = {p.id for p in projects}
        missing = set(id_list) - found_ids
        raise HTTPException(status_code=404, detail=f"Projects not found: {list(missing)}")

    project_summaries: list[dict[str, Any]] = []
    for p in projects:
        res = json.loads(p.results_json)
        req = json.loads(p.requirements_json)
        bal = res.get("variants", {}).get("balanced", {})
        project_summaries.append({
            "id": p.id,
            "name": p.name,
            "org_type": p.org_type,
            "created_at": p.created_at.isoformat(),
            "floors": req.get("floors"),
            "total_users": sum(d.get("users", 0) for d in req.get("departments", [])),
            "topology": bal.get("topology"),
            "total_cost": bal.get("cost", {}).get("total_cost"),
            "device_count": sum(d.get("quantity", 0) for d in bal.get("devices", [])),
            "routing": bal.get("routing", {}).get("protocol"),
            "subnets_count": len(bal.get("subnets", [])),
        })

    # Metric comparison rows
    comparison_metrics = [
        {
            "metric": "org_type",
            "label": "Organization Type",
            "values": {p["name"]: p["org_type"].title() for p in project_summaries},
        },
        {
            "metric": "floors",
            "label": "Campus Floors",
            "values": {p["name"]: p["floors"] for p in project_summaries},
        },
        {
            "metric": "total_users",
            "label": "Total Headcount",
            "values": {p["name"]: p["total_users"] for p in project_summaries},
        },
        {
            "metric": "topology",
            "label": "Selected Topology",
            "values": {p["name"]: p["topology"].replace("_", " ").title() for p in project_summaries},
        },
        {
            "metric": "total_cost",
            "label": "Estimated Cost (Balanced)",
            "values": {p["name"]: f"${p['total_cost']:,.2f}" for p in project_summaries},
        },
        {
            "metric": "device_count",
            "label": "Total Hardware Units",
            "values": {p["name"]: p["device_count"] for p in project_summaries},
        },
        {
            "metric": "routing",
            "label": "Routing Protocol",
            "values": {p["name"]: p["routing"] for p in project_summaries},
        },
    ]

    return ProjectCompareResponse(
        projects=project_summaries,
        comparison_metrics=comparison_metrics,
    )


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(project_id: int, db: Session = Depends(get_db)) -> ProjectDetail:
    """Loads a specific saved project by ID."""
    p = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    req_obj = RequirementsInput.model_validate_json(p.requirements_json)
    res_obj = DesignGenerateResponse.model_validate_json(p.results_json)

    return ProjectDetail(
        id=p.id,
        name=p.name,
        org_type=p.org_type,
        created_at=p.created_at,
        requirements=req_obj,
        results=res_obj,
        explanation_source=p.explanation_source,
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """Deletes a saved project by ID."""
    p = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    db.delete(p)
    db.commit()
    return None


"""
routes_export.py — API endpoints for CLI config ZIP and PDF report export.
Spec Section 10: POST /api/export/pdf and POST /api/export/config.
"""
from __future__ import annotations

import io
import zipfile
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.schemas.design import DesignResult
from app.exporters.cli_config import generate_cli_configs
from app.exporters.pdf_report import generate_pdf_report

router = APIRouter(prefix="/api/export", tags=["export"])


# ── Request models ──────────────────────────────────────────────────────────

class ExportPdfRequest(BaseModel):
    design: DesignResult
    requirements: dict[str, Any]
    comparison: list[dict[str, Any]] | None = None
    comparison_summary: str = ""
    diagram_png_b64: str | None = None   # Base64-encoded PNG from browser (optional)


class ExportConfigRequest(BaseModel):
    design: DesignResult


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.post("/pdf")
def export_pdf(payload: ExportPdfRequest) -> Response:
    """
    Generate a multi-section PDF design report.

    If diagram_png_b64 is provided (Base64-encoded PNG from the React Flow
    canvas), it is embedded in the topology section.  Otherwise, the backend
    renders a static diagram using NetworkX + Matplotlib.

    Returns: application/pdf binary.
    """
    try:
        pdf_bytes = generate_pdf_report(
            design=payload.design,
            requirements=payload.requirements,
            comparison=payload.comparison,
            comparison_summary=payload.comparison_summary,
            diagram_png_b64=payload.diagram_png_b64,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {str(exc)}",
        )

    org_name = payload.requirements.get("org_name", "network_design").replace(" ", "_")
    variant = payload.design.variant
    filename = f"{org_name}_{variant}_report.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/config")
def export_config(payload: ExportConfigRequest) -> Response:
    """
    Generate per-device Cisco IOS-style CLI configuration files and return
    them as a ZIP archive.

    Returns: application/zip binary.
    """
    try:
        configs = generate_cli_configs(payload.design)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"CLI config generation failed: {str(exc)}",
        )

    # Pack all text files into a ZIP in memory
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for filename, content in configs.items():
            zf.writestr(filename, content.encode("utf-8"))

    zip_buf.seek(0)
    zip_bytes = zip_buf.read()

    variant = payload.design.variant
    archive_name = f"cli_configs_{variant}.zip"

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{archive_name}"'},
    )


@router.post("/diagram-png")
def export_diagram_png(payload: ExportConfigRequest) -> Response:
    """
    Generate a static network topology diagram as PNG.

    Returns: image/png binary.
    """
    from app.exporters.diagram_image import generate_diagram_png
    try:
        png_bytes = generate_diagram_png(
            payload.design.graph,
            title=f"Network Topology ({payload.design.variant.upper()})"
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Diagram PNG generation failed: {str(exc)}",
        )

    variant = payload.design.variant
    filename = f"topology_{variant}.png"

    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


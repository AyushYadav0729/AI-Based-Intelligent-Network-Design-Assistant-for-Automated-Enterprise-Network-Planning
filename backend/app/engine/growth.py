"""
growth.py — Computes planned growth for departments and users.
Spec Section 6.1:
planned_users(dept) = ceil(dept.users * (1 + growth_percent/100))
Stores both current and planned values.
"""
from dataclasses import dataclass
import math
from app.schemas.requirements import RequirementsInput, Department


@dataclass(frozen=True)
class PlannedDepartment:
    name: str
    current_users: int
    planned_users: int
    floor: int
    dept_type: str
    security_level: str
    needs_guest_access: bool
    wired_printers: int
    notes: str


@dataclass(frozen=True)
class GrowthProjection:
    departments: list[PlannedDepartment]
    current_total_users: int
    planned_total_users: int
    growth_percent: float
    growth_years: int


def calculate_growth(req: RequirementsInput) -> GrowthProjection:
    """Calculates planned user headcounts per department and totals."""
    growth_factor = 1.0 + (req.growth_percent / 100.0)
    planned_depts: list[PlannedDepartment] = []

    for dept in req.departments:
        planned_count = math.ceil(dept.users * growth_factor)
        planned_depts.append(
            PlannedDepartment(
                name=dept.name,
                current_users=dept.users,
                planned_users=planned_count,
                floor=dept.floor,
                dept_type=dept.dept_type,
                security_level=dept.security_level,
                needs_guest_access=dept.needs_guest_access,
                wired_printers=dept.wired_printers,
                notes=dept.notes,
            )
        )

    current_total = sum(d.users for d in req.departments)
    planned_total = sum(d.planned_users for d in planned_depts)

    return GrowthProjection(
        departments=planned_depts,
        current_total_users=current_total,
        planned_total_users=planned_total,
        growth_percent=req.growth_percent,
        growth_years=req.growth_years,
    )


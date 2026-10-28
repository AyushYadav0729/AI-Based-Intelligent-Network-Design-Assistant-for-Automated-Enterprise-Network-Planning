"""
cost.py — Deterministic cost estimation, licenses, cabling, and rack/UPS calculations.
Spec Section 6.11.
"""
from dataclasses import dataclass
import math
from typing import Any

from app.config import (
    COST_PER_DROP_USD,
    RACK_UPS_ALLOWANCE_USD,
    CURRENCY,
)
from app.schemas.requirements import RequirementsInput
from app.schemas.design import DeviceItem, Decision
from app.schemas.catalog import DeviceCatalog
from app.catalog.loader import get_catalog, get_device_by_id
from app.engine.growth import GrowthProjection


@dataclass(frozen=True)
class CostEstimate:
    devices_cost: float
    licenses_cost: float
    cabling_cost: float
    rack_ups_cost: float
    total_cost: float
    currency: str
    budget: float | None
    within_budget: bool
    budget_delta: float | None
    decision: Decision

    def to_dict(self) -> dict[str, Any]:
        return {
            "devices_cost": self.devices_cost,
            "licenses_cost": self.licenses_cost,
            "cabling_cost": self.cabling_cost,
            "rack_ups_cost": self.rack_ups_cost,
            "total_cost": self.total_cost,
            "currency": self.currency,
            "budget": self.budget,
            "within_budget": self.within_budget,
            "budget_delta": self.budget_delta,
        }


def calculate_cost(
    req: RequirementsInput,
    growth: GrowthProjection,
    devices: list[DeviceItem],
    topology: str,
    catalog: DeviceCatalog | None = None,
) -> CostEstimate:
    """
    Calculates hardware, licensing, cabling, and power/rack infrastructure cost.
    Spec Section 6.11.
    """
    cat = catalog or get_catalog()

    # 1. Hardware cost
    devices_cost = sum(d.total_price for d in devices)

    # 2. Software / threat licensing cost (from catalog)
    licenses_cost = 0.0
    for d in devices:
        cat_dev = get_device_by_id(d.catalog_id, cat)
        if cat_dev and cat_dev.license_price > 0:
            licenses_cost += cat_dev.license_price * d.quantity

    # 3. Cabling drops cost (per planned wired user port)
    total_wired_users = sum(d.planned_users for d in growth.departments)
    cabling_cost = round(total_wired_users * COST_PER_DROP_USD, 2)

    # 4. Rack / UPS unit allowance
    access_count = sum(d.quantity for d in devices if d.role == "access")
    racks_count = max(1, math.ceil(access_count / 4)) + (2 if topology == "three_tier" else 1)
    rack_ups_cost = round(racks_count * RACK_UPS_ALLOWANCE_USD, 2)

    total_cost = round(devices_cost + licenses_cost + cabling_cost + rack_ups_cost, 2)

    within_budget = True
    budget_delta = None
    if req.budget is not None:
        within_budget = total_cost <= req.budget
        budget_delta = round(req.budget - total_cost, 2)

    decision = Decision(
        stage="cost",
        choice=f"Total cost: ${total_cost:,.2f} {CURRENCY}",
        reason_code="COST_ESTIMATE_CALCULATED",
        params={
            "devices_cost": devices_cost,
            "licenses_cost": licenses_cost,
            "cabling_cost": cabling_cost,
            "rack_ups_cost": rack_ups_cost,
            "total_cost": total_cost,
            "budget": req.budget,
            "within_budget": within_budget,
        },
    )

    return CostEstimate(
        devices_cost=round(devices_cost, 2),
        licenses_cost=round(licenses_cost, 2),
        cabling_cost=cabling_cost,
        rack_ups_cost=rack_ups_cost,
        total_cost=total_cost,
        currency=CURRENCY,
        budget=req.budget,
        within_budget=within_budget,
        budget_delta=budget_delta,
        decision=decision,
    )


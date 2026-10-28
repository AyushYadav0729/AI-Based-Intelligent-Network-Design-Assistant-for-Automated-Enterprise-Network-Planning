"""
test_schemas_and_catalog.py — Tests for Pydantic schemas, scenario loading, and catalog validation.
Acceptance criteria for Phase 2:
- Sample scenario JSONs validate against RequirementsInput.
- Catalog loads and validates.
"""
from pathlib import Path
import json
import pytest

from app.schemas.requirements import RequirementsInput, Department, ServerSpec
from app.schemas.validation import ValidationIssue
from app.schemas.design import (
    Vlan,
    Subnet,
    DeviceItem,
    Decision,
    DesignResult,
    DesignGenerateResponse,
)
from app.schemas.catalog import DeviceCatalog, CatalogDevice
from app.catalog.loader import (
    load_catalog,
    get_catalog,
    get_devices_by_role,
    get_device_by_id,
)

SCENARIOS_DIR = Path(__file__).parent / "scenarios"


@pytest.mark.parametrize(
    "scenario_name",
    [
        "small_office.json",
        "school.json",
        "hospital.json",
        "it_company.json",
    ],
)
def test_scenario_validates_against_requirements_input(scenario_name: str):
    scenario_path = SCENARIOS_DIR / scenario_name
    assert scenario_path.exists(), f"Scenario file not found: {scenario_path}"

    with open(scenario_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate against RequirementsInput
    req = RequirementsInput.model_validate(data)
    assert req.org_name
    assert req.floors > 0
    assert len(req.departments) > 0
    assert req.servers.count >= 0
    assert req.base_network


def test_catalog_loads_and_validates():
    catalog = load_catalog()
    assert isinstance(catalog, DeviceCatalog)
    assert catalog.currency == "USD"
    assert len(catalog.devices) >= 20


def test_catalog_covers_all_roles_and_tiers():
    catalog = get_catalog()
    required_roles = [
        "access",
        "distribution",
        "core",
        "firewall",
        "router",
        "ap",
        "wlc",
        "server_switch",
    ]
    tiers = {"low", "mid", "high"}

    for role in required_roles:
        matching = get_devices_by_role(role, catalog)
        assert len(matching) > 0, f"No catalog devices for role: {role}"
        present_tiers = {d.tier for d in matching}
        assert tiers.issubset(present_tiers), (
            f"Role {role} missing tiers: {tiers - present_tiers}"
        )


def test_catalog_query_helpers():
    catalog = get_catalog()
    dev = get_device_by_id("acc-24-poe-1g", catalog)
    assert dev is not None
    assert dev.role == "access"
    assert dev.ports.access == 24
    assert dev.poe is True

    non_existent = get_device_by_id("non-existent-device-xyz", catalog)
    assert non_existent is None


def test_design_and_validation_models():
    issue = ValidationIssue(
        code="ADDR_OVERLAP",
        severity="error",
        message="Subnets overlap",
        related=["VLAN 10", "VLAN 20"],
    )
    assert issue.code == "ADDR_OVERLAP"

    vlan = Vlan(vlan_id=10, name="MGMT", purpose="Management")
    subnet = Subnet(
        vlan_id=10,
        name="MGMT",
        network="10.0.10.0",
        prefix=24,
        mask="255.255.255.0",
        gateway="10.0.10.1",
        usable_hosts=254,
        required_hosts=10,
        utilization_pct=3.9,
        first_host="10.0.10.1",
        last_host="10.0.10.254",
        broadcast="10.0.10.255",
    )
    device = DeviceItem(
        role="access",
        catalog_id="acc-24-poe-1g",
        model="Generic 24-port",
        quantity=2,
        unit_price=900.0,
        total_price=1800.0,
        location="Floor 1",
    )
    decision = Decision(
        stage="topology",
        choice="collapsed_core",
        reason_code="TOPO_COLLAPSED_USERS",
        params={"planned_users": 200},
    )

    design_res = DesignResult(
        variant="balanced",
        topology="collapsed_core",
        vlans=[vlan],
        subnets=[subnet],
        p2p_links=[],
        devices=[device],
        routing={"protocol": "OSPF"},
        security={"firewall": True},
        bandwidth={"total_demand_mbps": 500},
        cost={"total": 1800.0},
        capacity={},
        graph={"nodes": [], "edges": []},
        decisions=[decision],
        validation=[issue],
    )

    response = DesignGenerateResponse(
        variants={"balanced": design_res},
        comparison=[{"metric": "total_cost", "balanced": 1800.0}],
        comparison_summary="Balanced configuration within budget.",
    )
    assert response.variants["balanced"].variant == "balanced"


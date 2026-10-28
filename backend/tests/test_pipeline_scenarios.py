"""
test_pipeline_scenarios.py — End-to-end tests for all 4 scenarios through the design pipeline.
Acceptance criteria for Phase 4:
- All four scenarios generate a full DesignResult for one variant deterministically.
- Determinism check: running twice produces identical JSON.
- Verifies expected topology, routing, and device counts.
"""
from pathlib import Path
import json
import pytest

from app.schemas.requirements import RequirementsInput
from app.schemas.design import DesignResult
from app.engine.pipeline import run_pipeline

SCENARIOS_DIR = Path(__file__).parent / "scenarios"


def load_scenario(filename: str) -> RequirementsInput:
    with open(SCENARIOS_DIR / filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return RequirementsInput.model_validate(data)


def test_small_office_scenario():
    """Small office -> star topology, static routing, single uplink."""
    req = load_scenario("small_office.json")
    result = run_pipeline(req, variant="balanced")

    assert isinstance(result, DesignResult)
    assert result.topology == "star"
    assert result.routing["protocol"] == "static"
    assert len(result.subnets) >= 4  # 3 depts + servers + mgmt
    assert len(result.devices) > 0
    assert result.cost["total_cost"] > 0
    assert len(result.graph["nodes"]) > 0
    assert len(result.graph["edges"]) > 0


def test_school_scenario():
    """School -> collapsed_core topology, OSPF routing, dual uplinks."""
    req = load_scenario("school.json")
    result = run_pipeline(req, variant="balanced")

    assert isinstance(result, DesignResult)
    assert result.topology == "collapsed_core"
    assert result.routing["protocol"] == "OSPF"
    assert any(s.name == "DMZ" for s in result.subnets)
    assert any(s.name == "GUEST" for s in result.subnets)
    assert any(s.name == "WIFI-CORP" for s in result.subnets)


def test_hospital_scenario():
    """Hospital -> collapsed_core/three_tier, full_ha, HSRP, 802.1X security policies."""
    req = load_scenario("hospital.json")
    result = run_pipeline(req, variant="balanced")

    assert isinstance(result, DesignResult)
    assert result.topology in ["collapsed_core", "three_tier"]
    assert result.routing["protocol"] == "OSPF"

    # Full HA checks
    cores = [d for d in result.devices if d.role == "core"]
    assert sum(d.quantity for d in cores) == 2

    firewalls = [d for d in result.devices if d.role == "firewall"]
    assert sum(d.quantity for d in firewalls) == 2

    # Verify HSRP in subnets
    for s in result.subnets:
        assert s.hsrp is not None
        assert "virtual" in s.hsrp

    # Critical departments must have 802.1X
    policies = result.security["dept_policies"]
    emergency_policy = next(p for p in policies if p["dept_name"] == "Emergency")
    assert emergency_policy["dot1x_enabled"] is True


def test_it_company_scenario():
    """IT company -> 6 floors, 400+ engineers -> three_tier topology, OSPF."""
    req = load_scenario("it_company.json")
    result = run_pipeline(req, variant="balanced")

    assert isinstance(result, DesignResult)
    assert result.topology == "three_tier"
    assert result.routing["protocol"] == "OSPF"

    # Distribution switches present
    dist_switches = [d for d in result.devices if d.role == "distribution"]
    assert len(dist_switches) > 0


def test_pipeline_determinism():
    """Running the pipeline twice on the same scenario must produce identical JSON."""
    req = load_scenario("hospital.json")

    run_1 = run_pipeline(req, variant="balanced")
    run_2 = run_pipeline(req, variant="balanced")

    json_1 = run_1.model_dump_json()
    json_2 = run_2.model_dump_json()

    assert json_1 == json_2, "Pipeline produced non-deterministic output for identical input!"

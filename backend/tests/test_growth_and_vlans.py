"""
test_growth_and_vlans.py — Unit tests for growth calculations and VLAN generation.
Spec Section 6.1 and 6.4.
"""
import pytest
from app.schemas.requirements import RequirementsInput, Department, ServerSpec
from app.engine.growth import calculate_growth
from app.engine.vlans import generate_vlan_plan


def test_calculate_growth():
    req = RequirementsInput(
        org_name="Growth Org",
        org_type="corporate",
        floors=2,
        departments=[
            Department(name="Eng", users=100, floor=1, dept_type="engineering", security_level="high"),
            Department(name="Sales", users=35, floor=0, dept_type="office", security_level="low"),
        ],
        servers=ServerSpec(count=5, public_facing=1),
        growth_percent=25.0,
        growth_years=3,
    )

    proj = calculate_growth(req)
    assert proj.current_total_users == 135
    # Eng: 100 * 1.25 = 125
    # Sales: 35 * 1.25 = 43.75 -> ceil = 44
    assert proj.departments[0].planned_users == 125
    assert proj.departments[1].planned_users == 44
    assert proj.planned_total_users == 169
    assert proj.growth_percent == 25.0
    assert proj.growth_years == 3


def test_generate_vlan_plan_basic_and_conditional():
    req = RequirementsInput(
        org_name="VLAN Test",
        org_type="corporate",
        floors=1,
        departments=[
            Department(name="Engineering", users=50, floor=0, dept_type="engineering", security_level="high"),
            Department(name="Human Resources", users=10, floor=0, dept_type="hr", security_level="medium"),
        ],
        servers=ServerSpec(count=2, public_facing=1),
        wifi_enabled=True,
        guest_wifi=True,
    )

    vlans = generate_vlan_plan(req)
    vlan_ids = [v.vlan_id for v in vlans]
    vlan_names = [v.name for v in vlans]

    # Standard infrastructure VLANs
    assert 10 in vlan_ids  # MGMT
    assert 20 in vlan_ids  # SERVERS
    assert 30 in vlan_ids  # DMZ (since public_facing = 1)
    assert 40 in vlan_ids  # GUEST (since guest_wifi = True)
    assert 50 in vlan_ids  # WIFI-CORP (since wifi_enabled = True)
    assert 100 in vlan_ids  # Engineering
    assert 110 in vlan_ids  # Human Resources
    assert 999 in vlan_ids  # NATIVE_BLACKHOLE

    # Check clean naming for HR
    assert "HUMAN_RESOURCES" in vlan_names

    # Test conditional omissions
    req_minimal = RequirementsInput(
        org_name="Minimal Org",
        org_type="corporate",
        floors=1,
        departments=[Department(name="Admin", users=10, floor=0, dept_type="office", security_level="low")],
        servers=ServerSpec(count=2, public_facing=0),
        wifi_enabled=False,
        guest_wifi=False,
    )
    min_vlans = generate_vlan_plan(req_minimal)
    min_ids = [v.vlan_id for v in min_vlans]
    assert 30 not in min_ids  # No DMZ
    assert 40 not in min_ids  # No Guest
    assert 50 not in min_ids  # No Wi-Fi
    assert 10 in min_ids      # MGMT always present
    assert 20 in min_ids      # SERVERS always present
    assert 100 in min_ids     # Admin
    assert 999 in min_ids     # NATIVE_BLACKHOLE always present


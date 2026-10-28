"""
test_bandwidth.py — Unit tests for bandwidth demand aggregation and link sizing.
Spec Section 15:
- demand aggregation
- speed selection
- oversubscription ratios and uplink upgrade fallback
"""
import pytest
from app.schemas.requirements import RequirementsInput, Department, ServerSpec
from app.engine.growth import calculate_growth
from app.engine.bandwidth import (
    analyze_bandwidth,
    select_link_speed,
    check_oversubscription,
)


def test_select_link_speed():
    # Target util 0.7: 1G handles up to 700 Mbps
    s1, c1, l1 = select_link_speed(500.0, target_util=0.7)
    assert s1 == 1000
    assert c1 == 1
    assert l1 == "1G"

    # Demand 800 Mbps exceeds 700 Mbps -> jumps to 10G
    s2, c2, l2 = select_link_speed(800.0, target_util=0.7)
    assert s2 == 10_000
    assert c2 == 1
    assert l2 == "10G"

    # Dual bundle: 1200 Mbps with channels allowed: 2x1G = 2000 * 0.7 = 1400 Mbps
    s3, c3, l3 = select_link_speed(1200.0, target_util=0.7, allow_channels=True)
    assert s3 == 1000
    assert c3 == 2
    assert l3 == "2x1G"


def test_oversubscription_calculation():
    # 20 downlinks of 1G = 20,000 Mbps against 1G uplink = 20:1 (ok)
    ratio, ok = check_oversubscription(
        downlink_ports_sum_mbps=20_000,
        uplink_capacity_mbps=1_000,
        max_ratio=20.0,
    )
    assert ratio == 20.0
    assert ok is True

    # 25 downlinks of 1G = 25,000 Mbps against 1G uplink = 25:1 (> 20:1 -> not ok)
    ratio2, ok2 = check_oversubscription(
        downlink_ports_sum_mbps=25_000,
        uplink_capacity_mbps=1_000,
        max_ratio=20.0,
    )
    assert ratio2 == 25.0
    assert ok2 is False


def test_bandwidth_aggregation_and_upgrade():
    req = RequirementsInput(
        org_name="Bandwidth Org",
        org_type="corporate",
        floors=2,
        departments=[
            # Media dept requires 40 Mbps/user
            Department(name="Media", users=50, floor=0, dept_type="media", security_level="medium"),
            Department(name="Support", users=20, floor=1, dept_type="support", security_level="low"),
        ],
        servers=ServerSpec(count=4, public_facing=1),
        internet_bandwidth_mbps=500,
        growth_percent=20.0,
    )

    growth = calculate_growth(req)
    analysis = analyze_bandwidth(req, growth, topology="collapsed_core")

    # Media planned users = 50 * 1.2 = 60. Demand = 60 * 40 * 0.6 = 1440 Mbps
    assert analysis.department_demands["Media"] == 1440.0
    assert analysis.total_access_demand_mbps > 1440.0
    assert analysis.core_demand_mbps > analysis.total_access_demand_mbps

    # Floor 0 has 1440 Mbps demand, so Floor 0 uplink must be upgraded to 10G
    fl0_link = next(l for l in analysis.links if "Floor_0" in l.link_name)
    assert fl0_link.selected_speed_mbps == 10_000
    assert fl0_link.speed_label in ["10G", "2x10G"]


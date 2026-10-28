"""
test_vlsm.py — Unit tests for the VLSM engine.
Spec Section 15:
- prefix selection for host counts (1, 2, 30, 31, 62, 63, 126, 510, 1000)
- sort-descending allocation
- alignment to subnet boundaries
- no overlaps between any allocated subnets
- pool exhaustion and auto-expansion
- gateway and HSRP addressing
- /30 P2P link allocation
"""
import ipaddress
import pytest

from app.schemas.requirements import RequirementsInput, Department, ServerSpec
from app.engine.vlsm import (
    calculate_prefix,
    allocate_vlsm,
    allocate_p2p_links,
    _try_allocate,
    SubnetRequest,
    PoolExhaustedError,
)
from app.engine.growth import calculate_growth
from app.engine.vlans import generate_vlan_plan


@pytest.mark.parametrize(
    "required_hosts, expected_prefix",
    [
        (1, 30),
        (2, 30),
        (30, 27),
        (31, 26),
        (62, 26),
        (63, 25),
        (126, 25),
        (510, 23),
        (1000, 22),
    ],
)
def test_prefix_selection(required_hosts: int, expected_prefix: int):
    prefix = calculate_prefix(required_hosts)
    assert prefix == expected_prefix
    # Verify usable hosts in IPv4: 2^(32 - prefix) - 2 >= required_hosts
    usable = (2 ** (32 - prefix)) - 2
    assert usable >= required_hosts


def test_worked_example_from_spec():
    """
    Verifies the exact worked example from Spec Section 6.5:
    Engineering: 300 required -> /23 -> 10.0.0.0/23, gateway 10.0.0.1
    Finance: 120 required -> /25 -> 10.0.2.0/25, gateway 10.0.2.1
    HR: 60 required -> /26 -> 10.0.2.128/26, gateway 10.0.2.129
    Reception: 25 required -> /27 -> 10.0.2.192/27, gateway 10.0.2.193
    """
    requests = [
        SubnetRequest(vlan_id=100, name="Engineering", current_hosts=300, planned_hosts=300, required_hosts=300),
        SubnetRequest(vlan_id=110, name="Finance", current_hosts=120, planned_hosts=120, required_hosts=120),
        SubnetRequest(vlan_id=120, name="HR", current_hosts=60, planned_hosts=60, required_hosts=60),
        SubnetRequest(vlan_id=130, name="Reception", current_hosts=25, planned_hosts=25, required_hosts=25),
    ]

    subnets, capacity = _try_allocate(requests, pool_str="10.0.0.0/16", redundancy="none")
    by_name = {s.name: s for s in subnets}

    # 1. Engineering
    eng = by_name["Engineering"]
    assert eng.prefix == 23
    assert eng.network == "10.0.0.0"
    assert eng.gateway == "10.0.0.1"

    # 2. Finance
    fin = by_name["Finance"]
    assert fin.prefix == 25
    assert fin.network == "10.0.2.0"
    assert fin.gateway == "10.0.2.1"

    # 3. HR
    hr = by_name["HR"]
    assert hr.prefix == 26
    assert hr.network == "10.0.2.128"
    assert hr.gateway == "10.0.2.129"

    # 4. Reception
    rec = by_name["Reception"]
    assert rec.prefix == 27
    assert rec.network == "10.0.2.192"
    assert rec.gateway == "10.0.2.193"


def test_subnet_boundary_alignment_and_no_overlaps():
    """All subnets must be aligned to their natural power-of-2 boundaries and have 0 overlaps."""
    req = RequirementsInput(
        org_name="Test Org",
        org_type="corporate",
        floors=2,
        departments=[
            Department(name="Eng", users=150, floor=1, dept_type="engineering", security_level="high"),
            Department(name="Sales", users=45, floor=0, dept_type="office", security_level="low"),
            Department(name="Support", users=85, floor=0, dept_type="support", security_level="low"),
            Department(name="IT", users=15, floor=1, dept_type="datacenter_ops", security_level="critical"),
        ],
        servers=ServerSpec(count=10, public_facing=2),
        redundancy="dual_uplink",
        growth_percent=20.0,
        growth_years=3,
        base_network="10.0.0.0/16",
    )

    result = allocate_vlsm(req, p2p_count=4)
    all_nets = [ipaddress.ip_network(f"{s.network}/{s.prefix}") for s in result.subnets]
    p2p_nets = [ipaddress.ip_network(f"{s.network}/{s.prefix}") for s in result.p2p_links]

    # Verify boundary alignment
    for net in all_nets + p2p_nets:
        size = 2 ** (32 - net.prefixlen)
        assert int(net.network_address) % size == 0, f"{net} is not aligned to size {size}"

    # Verify no overlaps between any subnets (pairwise)
    combined = all_nets + p2p_nets
    for i in range(len(combined)):
        for j in range(i + 1, len(combined)):
            assert not combined[i].overlaps(combined[j]), (
                f"Overlap detected between {combined[i]} and {combined[j]}"
            )


def test_gateway_and_hsrp_addressing():
    """Under full_ha, HSRP addressing (first usable virtual, +1 active, +2 standby) must be assigned."""
    req_ha = RequirementsInput(
        org_name="HA Org",
        org_type="hospital",
        floors=2,
        departments=[
            Department(name="CriticalCare", users=50, floor=0, dept_type="support", security_level="critical")
        ],
        servers=ServerSpec(count=4, public_facing=1),
        redundancy="full_ha",
        base_network="10.0.0.0/16",
    )

    result_ha = allocate_vlsm(req_ha)
    for s in result_ha.subnets:
        net = ipaddress.ip_network(f"{s.network}/{s.prefix}")
        assert s.hsrp is not None
        assert s.hsrp["virtual"] == s.gateway
        assert s.hsrp["virtual"] == str(net.network_address + 1)
        assert s.hsrp["active"] == str(net.network_address + 2)
        assert s.hsrp["standby"] == str(net.network_address + 3)

    # Under none redundancy
    req_none = req_ha.model_copy(update={"redundancy": "none"})
    result_none = allocate_vlsm(req_none)
    for s in result_none.subnets:
        net = ipaddress.ip_network(f"{s.network}/{s.prefix}")
        assert s.hsrp is None
        assert s.gateway == str(net.network_address + 1)


def test_pool_exhaustion_and_auto_expansion():
    """When a small pool (e.g. /24) cannot fit requests, it auto-expands to /12 then /8."""
    req = RequirementsInput(
        org_name="Large Enterprise",
        org_type="corporate",
        floors=5,
        departments=[
            # Needs /22 (1000 hosts) -> cannot fit in /24
            Department(name="Heavy", users=800, floor=1, dept_type="engineering", security_level="medium"),
        ],
        servers=ServerSpec(count=10, public_facing=2),
        base_network="10.0.0.0/24",  # deliberately too small
    )

    result = allocate_vlsm(req)
    assert result.active_pool in ["10.0.0.0/12", "10.0.0.0/8"]
    assert len(result.decisions) == 1
    assert result.decisions[0].reason_code == "ADDR_POOL_EXPANDED"


def test_pool_exhaustion_raises_error():
    """When subnets exceed even /8, PoolExhaustedError is raised."""
    # Create an impossible requirement (> 16 million hosts)
    massive_depts = [
        Department(name=f"Dept{i}", users=2_000_000, floor=1, dept_type="engineering", security_level="low")
        for i in range(10)
    ]
    req = RequirementsInput(
        org_name="Planet Corp",
        org_type="corporate",
        floors=1,
        departments=massive_depts,
        servers=ServerSpec(count=1, public_facing=0),
        base_network="10.0.0.0/16",
    )

    with pytest.raises(PoolExhaustedError):
        allocate_vlsm(req)


def test_p2p_allocation():
    """Verifies that point-to-point links are allocated as /30s from the top of the pool."""
    p2p_subnets = allocate_p2p_links(count=5, pool_str="10.0.0.0/16")
    assert len(p2p_subnets) == 5

    for s in p2p_subnets:
        assert s.prefix == 30
        assert s.usable_hosts == 2
        assert s.required_hosts == 2
        assert s.network.startswith("10.0.255.")

    assert p2p_subnets[0].network == "10.0.255.0"
    assert p2p_subnets[1].network == "10.0.255.4"
    assert p2p_subnets[2].network == "10.0.255.8"
    assert p2p_subnets[3].network == "10.0.255.12"
    assert p2p_subnets[4].network == "10.0.255.16"

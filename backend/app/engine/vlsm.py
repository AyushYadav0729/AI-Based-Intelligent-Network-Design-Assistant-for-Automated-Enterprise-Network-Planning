"""
vlsm.py — Deterministic Variable-Length Subnet Masking (VLSM) allocator.
Spec Section 6.5.
All networking math uses Python's `ipaddress` module.
Never hand-rolls bit math where `ipaddress` can do it.
"""
import ipaddress
import math
from dataclasses import dataclass
from typing import Literal

from app.config import (
    BASE_NETWORK_DEFAULT,
    POOL_EXPANSION_ORDER,
    P2P_LINK_PREFIX,
    MGMT_DEFAULT_HOSTS,
    GUEST_USER_RATIO,
    CLIENTS_PER_AP,
)
from app.schemas.requirements import RequirementsInput
from app.schemas.design import Subnet, Decision, Vlan
from app.engine.growth import GrowthProjection, calculate_growth
from app.engine.vlans import generate_vlan_plan


class PoolExhaustedError(Exception):
    """Raised when address space cannot accommodate requested subnets."""
    pass


@dataclass(frozen=True)
class SubnetRequest:
    vlan_id: int | None
    name: str
    current_hosts: int
    planned_hosts: int
    required_hosts: int


@dataclass(frozen=True)
class VlsmResult:
    subnets: list[Subnet]
    p2p_links: list[Subnet]
    decisions: list[Decision]
    capacity: dict[str, dict[str, float | int]]
    active_pool: str


def calculate_prefix(required_hosts: int) -> int:
    """
    Computes the IPv4 prefix length needed to accommodate required_hosts.
    prefix = 32 - ceil(log2(required_hosts + 2))
    Clamped to maximum prefix /30.
    """
    if required_hosts <= 0:
        return 30
    needed_total_ips = required_hosts + 2  # 1 for network, 1 for broadcast
    bits = math.ceil(math.log2(needed_total_ips))
    prefix = 32 - bits
    if prefix > 30:
        prefix = 30
    if prefix < 0:
        raise ValueError(f"Required hosts {required_hosts} exceeds IPv4 address space")
    return prefix


def build_subnet_requests(
    req: RequirementsInput,
    growth: GrowthProjection,
    vlans: list[Vlan],
) -> list[SubnetRequest]:
    """
    Constructs the list of subnet requests for all active VLANs.
    Spec Section 6.5 step 1.
    """
    gw_count = 3 if req.redundancy == "full_ha" else 1
    requests: list[SubnetRequest] = []

    # Map department by name for quick lookup
    dept_map = {d.name: d for d in growth.departments}

    for vlan in vlans:
        # VLAN 999 is unrouted blackhole / native VLAN — no IP subnet
        if vlan.vlan_id == 999:
            continue

        if vlan.vlan_id == 10:
            # Management VLAN
            current_h = MGMT_DEFAULT_HOSTS
            est_aps = math.ceil(growth.planned_total_users * req.wifi_user_ratio / CLIENTS_PER_AP)
            planned_h = max(MGMT_DEFAULT_HOSTS, (req.floors * 4) + est_aps)
            requests.append(
                SubnetRequest(
                    vlan_id=10,
                    name=vlan.name,
                    current_hosts=current_h,
                    planned_hosts=planned_h,
                    required_hosts=planned_h + gw_count,
                )
            )
        elif vlan.vlan_id == 20:
            # Internal Servers
            cnt = req.servers.count
            requests.append(
                SubnetRequest(
                    vlan_id=20,
                    name=vlan.name,
                    current_hosts=cnt,
                    planned_hosts=cnt,
                    required_hosts=max(2, cnt) + gw_count,
                )
            )
        elif vlan.vlan_id == 30:
            # DMZ
            pub = req.servers.public_facing
            requests.append(
                SubnetRequest(
                    vlan_id=30,
                    name=vlan.name,
                    current_hosts=pub,
                    planned_hosts=pub,
                    required_hosts=max(2, pub) + gw_count,
                )
            )
        elif vlan.vlan_id == 40:
            # Guest VLAN
            curr_g = math.ceil(growth.current_total_users * GUEST_USER_RATIO)
            plan_g = math.ceil(growth.planned_total_users * GUEST_USER_RATIO)
            requests.append(
                SubnetRequest(
                    vlan_id=40,
                    name=vlan.name,
                    current_hosts=curr_g,
                    planned_hosts=plan_g,
                    required_hosts=max(10, plan_g) + gw_count,
                )
            )
        elif vlan.vlan_id == 50:
            # Corporate Wi-Fi
            curr_w = math.ceil(growth.current_total_users * req.wifi_user_ratio)
            plan_w = math.ceil(growth.planned_total_users * req.wifi_user_ratio)
            requests.append(
                SubnetRequest(
                    vlan_id=50,
                    name=vlan.name,
                    current_hosts=curr_w,
                    planned_hosts=plan_w,
                    required_hosts=max(10, plan_w) + gw_count,
                )
            )
        elif vlan.dept and vlan.dept in dept_map:
            # Department wired subnet
            d = dept_map[vlan.dept]
            curr_d = d.current_users + d.wired_printers
            plan_d = d.planned_users + d.wired_printers
            requests.append(
                SubnetRequest(
                    vlan_id=vlan.vlan_id,
                    name=vlan.name,
                    current_hosts=curr_d,
                    planned_hosts=plan_d,
                    required_hosts=plan_d + gw_count,
                )
            )

    return requests


def _get_reserved_blocks(pool_network: ipaddress.IPv4Network) -> tuple[ipaddress.IPv4Network, ipaddress.IPv4Network]:
    """
    Returns (p2p_block, loopback_block) from the top /24s of the given pool.
    p2p_block is the last /24; loopback_block is the second-to-last /24.
    """
    broadcast_int = int(pool_network.broadcast_address)
    p2p_int = broadcast_int - 255
    loopback_int = p2p_int - 256
    p2p_net = ipaddress.IPv4Network((p2p_int, 24))
    loopback_net = ipaddress.IPv4Network((loopback_int, 24))
    return p2p_net, loopback_net


def _try_allocate(
    requests: list[SubnetRequest],
    pool_str: str,
    redundancy: str,
) -> tuple[list[Subnet], dict[str, dict[str, float | int]]]:
    """
    Attempts sequential aligned allocation of requests into pool_str.
    Raises PoolExhaustedError if the pool cannot fit all requests.
    """
    pool_net = ipaddress.IPv4Network(pool_str)
    p2p_block, loopback_block = _get_reserved_blocks(pool_net)

    # Sort descending by required_hosts, tie-break by vlan_id and name for strict reproducibility
    sorted_requests = sorted(
        requests,
        key=lambda r: (-r.required_hosts, r.vlan_id or 0, r.name),
    )

    allocated_subnets: list[Subnet] = []
    capacity_table: dict[str, dict[str, float | int]] = {}

    current_int = int(pool_net.network_address)
    host_limit_int = int(loopback_block.network_address)  # Do not cross into reserved loopback / P2P blocks

    for req in sorted_requests:
        prefix = calculate_prefix(req.required_hosts)
        subnet_size = 2 ** (32 - prefix)

        # Align to subnet boundary
        if current_int % subnet_size != 0:
            current_int += subnet_size - (current_int % subnet_size)

        allocated_network = ipaddress.IPv4Network((current_int, prefix))

        # Check bounds
        if int(allocated_network.broadcast_address) >= host_limit_int:
            raise PoolExhaustedError(
                f"Subnet {req.name} ({req.required_hosts} hosts, /{prefix}) exceeds available space in {pool_str}"
            )

        # Advance current pointer
        current_int = int(allocated_network.broadcast_address) + 1

        usable_hosts = allocated_network.num_addresses - 2
        net_str = str(allocated_network.network_address)
        mask_str = str(allocated_network.netmask)
        bcast_str = str(allocated_network.broadcast_address)
        first_h = str(allocated_network.network_address + 1)
        last_h = str(allocated_network.broadcast_address - 1)
        util_pct = round((req.required_hosts / usable_hosts) * 100.0, 1)

        # Gateway & HSRP
        if redundancy == "full_ha":
            gateway_str = str(allocated_network.network_address + 1)
            hsrp_dict = {
                "virtual": str(allocated_network.network_address + 1),
                "active": str(allocated_network.network_address + 2),
                "standby": str(allocated_network.network_address + 3),
            }
        else:
            gateway_str = str(allocated_network.network_address + 1)
            hsrp_dict = None

        subnet_obj = Subnet(
            vlan_id=req.vlan_id,
            name=req.name,
            network=net_str,
            prefix=prefix,
            mask=mask_str,
            gateway=gateway_str,
            usable_hosts=usable_hosts,
            required_hosts=req.required_hosts,
            utilization_pct=util_pct,
            first_host=first_h,
            last_host=last_h,
            broadcast=bcast_str,
            hsrp=hsrp_dict,
        )
        allocated_subnets.append(subnet_obj)

        # Capacity metrics
        if req.current_hosts > 0:
            max_growth_pct = round(
                ((usable_hosts - req.current_hosts) / req.current_hosts) * 100.0, 1
            )
        else:
            max_growth_pct = 0.0

        capacity_table[req.name] = {
            "current_hosts": req.current_hosts,
            "planned_hosts": req.planned_hosts,
            "usable_hosts": usable_hosts,
            "utilization_pct": util_pct,
            "max_growth_percent_before_exhaustion": max_growth_pct,
        }

    return allocated_subnets, capacity_table


def allocate_p2p_links(
    count: int,
    pool_str: str,
) -> list[Subnet]:
    """
    Allocates point-to-point /30 subnets from the dedicated P2P block (last /24 of the pool).
    Spec Section 6.5 step 4.
    """
    if count <= 0:
        return []

    pool_net = ipaddress.IPv4Network(pool_str)
    p2p_block, _ = _get_reserved_blocks(pool_net)

    p2p_subnets: list[Subnet] = []
    p2p_gen = p2p_block.subnets(new_prefix=P2P_LINK_PREFIX)

    for i in range(count):
        try:
            link_net = next(p2p_gen)
        except StopIteration:
            raise PoolExhaustedError(f"P2P block {p2p_block} exhausted at link {i + 1}")

        first_h = str(link_net.network_address + 1)
        last_h = str(link_net.network_address + 2)

        p2p_subnets.append(
            Subnet(
                vlan_id=None,
                name=f"P2P_LINK_{i + 1}",
                network=str(link_net.network_address),
                prefix=P2P_LINK_PREFIX,
                mask=str(link_net.netmask),
                gateway=first_h,
                usable_hosts=2,
                required_hosts=2,
                utilization_pct=100.0,
                first_host=first_h,
                last_host=last_h,
                broadcast=str(link_net.broadcast_address),
                hsrp=None,
            )
        )

    return p2p_subnets


def allocate_vlsm(
    req: RequirementsInput,
    growth: GrowthProjection | None = None,
    vlans: list[Vlan] | None = None,
    p2p_count: int = 0,
) -> VlsmResult:
    """
    Full VLSM pipeline: builds requests, allocates with auto-expansion if exhausted,
    allocates P2P blocks, and records decisions.
    Spec Section 6.5.
    """
    growth_proj = growth or calculate_growth(req)
    vlan_list = vlans or generate_vlan_plan(req)
    requests = build_subnet_requests(req, growth_proj, vlan_list)

    candidate_pools = [req.base_network] + [
        p for p in POOL_EXPANSION_ORDER if p != req.base_network
    ]

    decisions: list[Decision] = []
    allocated_subnets: list[Subnet] = []
    capacity_table: dict[str, dict[str, float | int]] = {}
    active_pool = req.base_network

    for pool in candidate_pools:
        try:
            allocated_subnets, capacity_table = _try_allocate(
                requests=requests,
                pool_str=pool,
                redundancy=req.redundancy,
            )
            active_pool = pool
            if pool != req.base_network:
                decisions.append(
                    Decision(
                        stage="vlsm",
                        choice=pool,
                        reason_code="ADDR_POOL_EXPANDED",
                        params={"original_pool": req.base_network, "expanded_pool": pool},
                    )
                )
            break
        except PoolExhaustedError:
            continue
    else:
        # None of the candidate pools could fit the requests
        raise PoolExhaustedError(
            f"All candidate pools ({candidate_pools}) exhausted for requested subnets."
        )

    # Allocate P2P links from active pool
    p2p_subnets = allocate_p2p_links(p2p_count, active_pool)

    return VlsmResult(
        subnets=allocated_subnets,
        p2p_links=p2p_subnets,
        decisions=decisions,
        capacity=capacity_table,
        active_pool=active_pool,
    )


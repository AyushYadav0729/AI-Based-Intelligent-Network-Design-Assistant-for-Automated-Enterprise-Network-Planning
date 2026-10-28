"""
bandwidth.py — Bandwidth demand aggregation, link speed selection, and oversubscription analysis.
Spec Section 6.2.
"""
from dataclasses import dataclass
from typing import Any
import math

from app.config import (
    TRAFFIC_PROFILE_MBPS,
    CONCURRENCY,
    LINK_SPEEDS_MBPS,
    TARGET_UTIL_BALANCED,
    OVERSUB_ACCESS_TO_DIST_MAX,
    OVERSUB_DIST_TO_CORE_MAX,
)
from app.engine.growth import GrowthProjection
from app.schemas.requirements import RequirementsInput
from app.schemas.design import Decision


@dataclass(frozen=True)
class LinkBandwidthSpec:
    link_name: str
    demand_mbps: float
    selected_speed_mbps: int
    speed_label: str
    channels: int
    total_capacity_mbps: int
    utilization_pct: float
    oversubscription_ratio: float
    oversubscription_ok: bool


@dataclass(frozen=True)
class BandwidthAnalysis:
    department_demands: dict[str, float]
    floor_demands: dict[int, float]
    total_access_demand_mbps: float
    server_traffic_mbps: float
    internet_bandwidth_mbps: float
    core_demand_mbps: float
    links: list[LinkBandwidthSpec]
    decisions: list[Decision]


def format_speed_label(speed_mbps: int, channels: int = 1) -> str:
    """Formats Mbps into human-readable speed label like '1G', '10G', '2x10G', '40G'."""
    base_speed = (
        f"{speed_mbps // 1000}G" if speed_mbps >= 1000 else f"{speed_mbps}M"
    )
    if channels > 1:
        return f"{channels}x{base_speed}"
    return base_speed


def select_link_speed(
    demand_mbps: float,
    target_util: float = TARGET_UTIL_BALANCED,
    allow_channels: bool = False,
    forced_min_speed: int = 1_000,
) -> tuple[int, int, str]:
    """
    Selects link speed class and optional channel bundle.
    Spec Section 6.2: Use EtherChannel bundles (e.g. 2x10G) before jumping speed class.
    """
    speeds = [s for s in LINK_SPEEDS_MBPS if s >= forced_min_speed]

    for s in speeds:
        # Check single link of this speed class
        if demand_mbps <= (target_util * s):
            return s, 1, format_speed_label(s, 1)
        # Check 2x channel bundle before jumping to next speed class
        if allow_channels and demand_mbps <= (target_util * s * 2):
            return s, 2, format_speed_label(s, 2)

    # If even 2x the highest speed class is exceeded, return max with 2 channels
    max_s = speeds[-1]
    channels = 2 if allow_channels else 1
    return max_s, channels, format_speed_label(max_s, channels)


def check_oversubscription(
    downlink_ports_sum_mbps: float,
    uplink_capacity_mbps: float,
    max_ratio: float,
) -> tuple[float, bool]:
    """Computes oversubscription ratio = downlinks / uplinks and verifies within limit."""
    if uplink_capacity_mbps <= 0:
        return 999.0, False
    ratio = round(downlink_ports_sum_mbps / uplink_capacity_mbps, 2)
    return ratio, ratio <= max_ratio


def analyze_bandwidth(
    req: RequirementsInput,
    growth: GrowthProjection,
    topology: str,
    target_util: float = TARGET_UTIL_BALANCED,
    force_10g_access: bool = False,
) -> BandwidthAnalysis:
    """
    Analyzes campus bandwidth requirements from departments up to the core.
    Spec Section 6.2.
    """
    dept_demands: dict[str, float] = {}
    floor_demands: dict[int, float] = {f: 0.0 for f in range(req.floors)}

    for dept in growth.departments:
        profile_mbps = TRAFFIC_PROFILE_MBPS.get(dept.dept_type, 5.0)
        demand = round(dept.planned_users * profile_mbps * CONCURRENCY, 2)
        dept_demands[dept.name] = demand
        fl = min(dept.floor, req.floors - 1)
        floor_demands[fl] = round(floor_demands.get(fl, 0.0) + demand, 2)

    total_access_demand = round(sum(dept_demands.values()), 2)
    # Server traffic estimation: 25 Mbps per internal server + public DMZ traffic
    server_traffic = round(
        (req.servers.count * 25.0) + (req.servers.public_facing * 50.0), 2
    )
    internet_bw = float(req.internet_bandwidth_mbps)
    core_demand = round(total_access_demand + server_traffic + internet_bw, 2)

    allow_bundles = req.redundancy in ["dual_uplink", "full_ha"]
    min_access_speed = 10_000 if force_10g_access else 1_000

    links: list[LinkBandwidthSpec] = []
    decisions: list[Decision] = []

    # 1. Access Uplinks (per floor)
    for floor_num, demand in floor_demands.items():
        speed, channels, label = select_link_speed(
            demand_mbps=demand,
            target_util=target_util,
            allow_channels=allow_bundles,
            forced_min_speed=min_access_speed,
        )
        total_capacity = speed * channels
        util_pct = (
            round((demand / total_capacity) * 100.0, 1) if total_capacity else 0.0
        )

        # Access switch downlink estimation: planned users on floor * 1G
        floor_wired_users = sum(
            d.planned_users for d in growth.departments if min(d.floor, req.floors - 1) == floor_num
        )
        downlink_sum_mbps = floor_wired_users * 1_000.0  # 1G per user port

        ratio, ok = check_oversubscription(
            downlink_ports_sum_mbps=downlink_sum_mbps,
            uplink_capacity_mbps=total_capacity,
            max_ratio=OVERSUB_ACCESS_TO_DIST_MAX,
        )

        # If oversubscribed, upgrade uplink if possible
        if not ok and speed < 10_000:
            speed, channels, label = 10_000, (2 if allow_bundles else 1), format_speed_label(10_000, 2 if allow_bundles else 1)
            total_capacity = speed * channels
            ratio, ok = check_oversubscription(
                downlink_ports_sum_mbps=downlink_sum_mbps,
                uplink_capacity_mbps=total_capacity,
                max_ratio=OVERSUB_ACCESS_TO_DIST_MAX,
            )

        links.append(
            LinkBandwidthSpec(
                link_name=f"Access_Floor_{floor_num}_Uplink",
                demand_mbps=demand,
                selected_speed_mbps=speed,
                speed_label=label,
                channels=channels,
                total_capacity_mbps=total_capacity,
                utilization_pct=util_pct,
                oversubscription_ratio=ratio,
                oversubscription_ok=ok,
            )
        )

    # 2. Distribution to Core or Core Interconnect
    if topology == "three_tier":
        dist_speed, dist_chan, dist_label = select_link_speed(
            demand_mbps=total_access_demand,
            target_util=target_util,
            allow_channels=allow_bundles,
            forced_min_speed=10_000,
        )
        dist_cap = dist_speed * dist_chan
        dist_ratio, dist_ok = check_oversubscription(
            downlink_ports_sum_mbps=sum(l.total_capacity_mbps for l in links),
            uplink_capacity_mbps=dist_cap,
            max_ratio=OVERSUB_DIST_TO_CORE_MAX,
        )
        if not dist_ok and dist_speed < 40_000:
            dist_speed, dist_chan, dist_label = 40_000, (2 if allow_bundles else 1), format_speed_label(40_000, 2 if allow_bundles else 1)
            dist_cap = dist_speed * dist_chan
            dist_ratio, dist_ok = check_oversubscription(
                downlink_ports_sum_mbps=sum(l.total_capacity_mbps for l in links),
                uplink_capacity_mbps=dist_cap,
                max_ratio=OVERSUB_DIST_TO_CORE_MAX,
            )

        links.append(
            LinkBandwidthSpec(
                link_name="Distribution_To_Core_Uplink",
                demand_mbps=total_access_demand,
                selected_speed_mbps=dist_speed,
                speed_label=dist_label,
                channels=dist_chan,
                total_capacity_mbps=dist_cap,
                utilization_pct=round((total_access_demand / dist_cap) * 100.0, 1),
                oversubscription_ratio=dist_ratio,
                oversubscription_ok=dist_ok,
            )
        )

    decisions.append(
        Decision(
            stage="bandwidth",
            choice=f"Core demand: {core_demand} Mbps",
            reason_code="BANDWIDTH_AGGREGATION_COMPUTED",
            params={
                "total_access_demand_mbps": total_access_demand,
                "server_traffic_mbps": server_traffic,
                "internet_bandwidth_mbps": internet_bw,
                "core_demand_mbps": core_demand,
                "target_utilization": target_util,
            },
        )
    )

    return BandwidthAnalysis(
        department_demands=dept_demands,
        floor_demands=floor_demands,
        total_access_demand_mbps=total_access_demand,
        server_traffic_mbps=server_traffic,
        internet_bandwidth_mbps=internet_bw,
        core_demand_mbps=core_demand,
        links=links,
        decisions=decisions,
    )

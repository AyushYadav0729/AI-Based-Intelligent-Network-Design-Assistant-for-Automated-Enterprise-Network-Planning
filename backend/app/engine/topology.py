"""
topology.py — Deterministic topology selection.
Spec Section 6.3.
Selects star, collapsed_core, or three_tier based on planned headcount, floors, and switch count.
"""
from dataclasses import dataclass
from app.config import (
    TOPO_STAR_MAX_USERS,
    TOPO_STAR_MAX_FLOORS,
    TOPO_COLLAPSED_MAX_USERS,
    TOPO_COLLAPSED_MAX_FLOORS,
    TOPO_COLLAPSED_MAX_ACCESS_SW,
)
from app.schemas.design import Decision


@dataclass(frozen=True)
class TopologySelection:
    topology: str
    decision: Decision


def select_topology(
    total_planned_users: int,
    floors: int,
    access_switch_count: int,
) -> TopologySelection:
    """
    Selects campus network topology deterministically according to spec Section 6.3.
    """
    params = {
        "total_planned_users": total_planned_users,
        "floors": floors,
        "access_switch_count": access_switch_count,
        "max_star_users": TOPO_STAR_MAX_USERS,
        "max_star_floors": TOPO_STAR_MAX_FLOORS,
        "max_collapsed_users": TOPO_COLLAPSED_MAX_USERS,
        "max_collapsed_floors": TOPO_COLLAPSED_MAX_FLOORS,
        "max_collapsed_access_sw": TOPO_COLLAPSED_MAX_ACCESS_SW,
    }

    if total_planned_users <= TOPO_STAR_MAX_USERS and floors <= TOPO_STAR_MAX_FLOORS:
        topology = "star"
        reason_code = "TOPO_STAR_SMALL_NETWORK"
    elif (
        total_planned_users <= TOPO_COLLAPSED_MAX_USERS
        and floors <= TOPO_COLLAPSED_MAX_FLOORS
        and access_switch_count <= TOPO_COLLAPSED_MAX_ACCESS_SW
    ):
        topology = "collapsed_core"
        reason_code = "TOPO_COLLAPSED_CORE_MID_NETWORK"
    else:
        topology = "three_tier"
        reason_code = "TOPO_THREE_TIER_LARGE_NETWORK"

    decision = Decision(
        stage="topology",
        choice=topology,
        reason_code=reason_code,
        params=params,
    )

    return TopologySelection(topology=topology, decision=decision)


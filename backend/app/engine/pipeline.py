"""
pipeline.py — Deterministic network design pipeline orchestrator.
Spec Section 6.
Runs all design stages sequentially as pure functions:
requirements -> growth -> vlans -> topology -> redundancy -> bandwidth -> devices -> routing -> security -> vlsm -> cost -> graph -> DesignResult.
"""
import math
from typing import Literal

from app.config import (
    PORT_HEADROOM_BUDGET,
    PORT_HEADROOM_BALANCED,
    PORT_HEADROOM_HIGH_PERF,
    TARGET_UTIL_BUDGET,
    TARGET_UTIL_BALANCED,
    TARGET_UTIL_HIGH_PERF,
)
from app.schemas.requirements import RequirementsInput
from app.schemas.design import DesignResult, Decision
from app.schemas.validation import ValidationIssue
from app.engine.growth import calculate_growth
from app.engine.vlans import generate_vlan_plan
from app.engine.topology import select_topology
from app.engine.redundancy import plan_redundancy
from app.engine.bandwidth import analyze_bandwidth
from app.engine.devices import size_devices
from app.engine.routing import recommend_routing
from app.engine.security import design_security
from app.engine.vlsm import allocate_vlsm
from app.engine.cost import calculate_cost
from app.engine.graph_builder import build_network_graph
from app.engine.validator import validate_design


def run_pipeline(
    req: RequirementsInput,
    variant: Literal["budget", "balanced", "high_performance"] = "balanced",
) -> DesignResult:
    """
    Executes the deterministic network design pipeline for a single variant.
    Returns a fully populated DesignResult.
    """
    all_decisions: list[Decision] = []

    # 1. Growth Projection
    growth = calculate_growth(req)

    # Preliminary access switch count estimate for topology thresholding
    est_access_sw = max(1, math.ceil(growth.planned_total_users / 35))

    # 2. Topology Selection
    topo_sel = select_topology(
        total_planned_users=growth.planned_total_users,
        floors=req.floors,
        access_switch_count=est_access_sw,
    )
    topology = topo_sel.topology
    all_decisions.append(topo_sel.decision)

    # 3. Redundancy Architecture
    # For high-performance, spec Section 6.10: redundancy is user's choice + one step up
    effective_req = req
    if variant == "high_performance":
        if req.redundancy == "none":
            effective_req = req.model_copy(update={"redundancy": "dual_uplink"})
        elif req.redundancy == "dual_uplink":
            effective_req = req.model_copy(update={"redundancy": "full_ha"})

    redundancy = plan_redundancy(effective_req, topology)
    all_decisions.append(redundancy.decision)

    # 4. Bandwidth Analysis & Link Sizing
    if variant == "budget":
        target_util = TARGET_UTIL_BUDGET
        tier = "low"
        headroom = PORT_HEADROOM_BUDGET
        force_10g = False
    elif variant == "high_performance":
        target_util = TARGET_UTIL_HIGH_PERF
        tier = "high"
        headroom = PORT_HEADROOM_HIGH_PERF
        force_10g = True
    else:  # balanced
        target_util = TARGET_UTIL_BALANCED
        tier = "mid"
        headroom = PORT_HEADROOM_BALANCED
        force_10g = False

    bw_analysis = analyze_bandwidth(
        req=effective_req,
        growth=growth,
        topology=topology,
        target_util=target_util,
        force_10g_access=force_10g,
    )
    all_decisions.extend(bw_analysis.decisions)

    # 5. VLAN Plan
    vlans = generate_vlan_plan(effective_req)

    # 6. Point-to-Point Link Sizing & VLSM Allocation
    # Determine P2P links needed for L3 interconnects
    if topology == "three_tier":
        dist_blocks = max(1, math.ceil(req.floors / 2))
        p2p_count = dist_blocks * redundancy.core_count + (1 if redundancy.core_count > 1 else 0)
    elif topology == "collapsed_core":
        p2p_count = 2 if redundancy.core_count > 1 else 1
    else:  # star
        p2p_count = 1

    vlsm_result = allocate_vlsm(
        req=effective_req,
        growth=growth,
        vlans=vlans,
        p2p_count=p2p_count,
    )
    all_decisions.extend(vlsm_result.decisions)

    # 7. Device Selection & Quantities from Catalog
    device_sizing = size_devices(
        req=effective_req,
        growth=growth,
        topology=topology,
        redundancy=redundancy,
        tier=tier,
        port_headroom=headroom,
    )
    all_decisions.extend(device_sizing.decisions)

    # 8. Routing Architecture
    l3_count = redundancy.core_count + (
        sum(d.quantity for d in device_sizing.items if d.role == "distribution")
    )
    routing = recommend_routing(
        req=effective_req,
        topology=topology,
        subnet_count=len(vlsm_result.subnets),
        l3_device_count=l3_count,
    )
    all_decisions.append(routing.decision)

    # 9. Security Design & ACL Matrix
    security = design_security(effective_req, vlans)
    all_decisions.extend(security.decisions)

    # 10. Cost Estimation
    cost = calculate_cost(
        req=effective_req,
        growth=growth,
        devices=device_sizing.items,
        topology=topology,
    )
    all_decisions.append(cost.decision)

    # 11. Graph Model (for React Flow / Diagram)
    core_link = next((l for l in bw_analysis.links if "Core" in l.link_name), None)
    access_link = next((l for l in bw_analysis.links if "Access" in l.link_name), None)
    speed_labels = {
        "core_uplink": core_link.speed_label if core_link else "10G",
        "dist_uplink": "10G",
        "access_uplink": access_link.speed_label if access_link else "1G",
    }
    graph = build_network_graph(
        req=effective_req,
        topology=topology,
        devices=device_sizing.items,
        speed_labels=speed_labels,
    )

    # Assemble candidate result for validation
    candidate = DesignResult(
        variant=variant,
        topology=topology,
        vlans=vlans,
        subnets=vlsm_result.subnets,
        p2p_links=vlsm_result.p2p_links,
        devices=device_sizing.items,
        routing=routing.to_dict(),
        security=security.to_dict(),
        bandwidth={
            "department_demands": bw_analysis.department_demands,
            "floor_demands": bw_analysis.floor_demands,
            "total_access_demand_mbps": bw_analysis.total_access_demand_mbps,
            "server_traffic_mbps": bw_analysis.server_traffic_mbps,
            "internet_bandwidth_mbps": bw_analysis.internet_bandwidth_mbps,
            "core_demand_mbps": bw_analysis.core_demand_mbps,
            "links": [
                {
                    "link_name": l.link_name,
                    "demand_mbps": l.demand_mbps,
                    "speed": l.speed_label,
                    "capacity_mbps": l.total_capacity_mbps,
                    "utilization_pct": l.utilization_pct,
                    "oversubscription_ratio": l.oversubscription_ratio,
                    "oversubscription_ok": l.oversubscription_ok,
                }
                for l in bw_analysis.links
            ],
        },
        cost=cost.to_dict(),
        capacity=vlsm_result.capacity,
        graph=graph,
        decisions=all_decisions,
        validation=[],
    )

    # Run deterministic rule-based validator (Spec Section 7)
    validation_issues = validate_design(candidate, effective_req)

    return candidate.model_copy(update={"validation": validation_issues})


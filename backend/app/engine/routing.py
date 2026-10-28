"""
routing.py — Deterministic routing architecture recommendation.
Spec Section 6.7.
"""
from dataclasses import dataclass
from typing import Any
from app.schemas.requirements import RequirementsInput
from app.schemas.design import Decision


@dataclass(frozen=True)
class RoutingPlan:
    protocol: str  # "static" or "OSPF"
    inter_vlan_method: str  # "SVI" or "router_on_a_stick"
    ospf_area: int | None
    passive_interfaces: list[str]
    default_route: str
    rip_evaluation_note: str
    decision: Decision

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol": self.protocol,
            "inter_vlan_method": self.inter_vlan_method,
            "ospf_area": self.ospf_area,
            "passive_interfaces": self.passive_interfaces,
            "default_route": self.default_route,
            "rip_evaluation_note": self.rip_evaluation_note,
        }


def recommend_routing(
    req: RequirementsInput,
    topology: str,
    subnet_count: int,
    l3_device_count: int,
) -> RoutingPlan:
    """
    Recommends deterministic routing protocol and inter-VLAN routing design.
    Spec Section 6.7.
    """
    is_small_star = (
        topology == "star" and subnet_count <= 8 and req.redundancy == "none"
    )
    is_small_l3 = (
        subnet_count <= 8 and l3_device_count <= 2 and req.redundancy == "none"
    )

    if is_small_star or is_small_l3:
        protocol = "static"
        inter_vlan = "router_on_a_stick" if topology == "star" else "SVI"
        ospf_area = None
        reason_code = "ROUTING_STATIC_SMALL_TOPOLOGY"
    else:
        protocol = "OSPF"
        inter_vlan = "SVI"
        ospf_area = 0
        reason_code = "ROUTING_OSPF_ENTERPRISE_CONVERGENCE"

    rip_note = (
        "RIP was evaluated and rejected: limited to 15 hops, slow convergence time, "
        "and periodic broadcasting causing higher network overhead compared to OSPF."
    )

    default_route = "ip route 0.0.0.0 0.0.0.0 [ISP_NEXT_HOP]"

    decision = Decision(
        stage="routing",
        choice=protocol,
        reason_code=reason_code,
        params={
            "protocol": protocol,
            "inter_vlan_method": inter_vlan,
            "subnet_count": subnet_count,
            "l3_device_count": l3_device_count,
            "topology": topology,
            "redundancy": req.redundancy,
        },
    )

    return RoutingPlan(
        protocol=protocol,
        inter_vlan_method=inter_vlan,
        ospf_area=ospf_area,
        passive_interfaces=["VLAN_SVIs"],
        default_route=default_route,
        rip_evaluation_note=rip_note,
        decision=decision,
    )


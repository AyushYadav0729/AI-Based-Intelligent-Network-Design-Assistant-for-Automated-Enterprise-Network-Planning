"""
redundancy.py — Redundancy plan and high-availability configuration.
Spec Section 6.9.
"""
from dataclasses import dataclass
from app.schemas.requirements import RequirementsInput
from app.schemas.design import Decision


@dataclass(frozen=True)
class RedundancyPlan:
    level: str  # "none", "dual_uplink", "full_ha"
    core_count: int
    firewall_count: int
    dist_pair: bool
    uplinks_per_access: int
    hsrp_enabled: bool
    etherchannel_enabled: bool
    decision: Decision


def plan_redundancy(req: RequirementsInput, topology: str) -> RedundancyPlan:
    """
    Computes device multipliers and HA features based on requested redundancy level.
    """
    level = req.redundancy

    if level == "full_ha":
        core_count = 2
        firewall_count = 2
        dist_pair = topology == "three_tier"
        uplinks_per_access = 2
        hsrp_enabled = True
        etherchannel_enabled = True
        reason_code = "REDUNDANCY_FULL_HA_ENABLED"
    elif level == "dual_uplink":
        core_count = 1
        firewall_count = 1
        dist_pair = False
        uplinks_per_access = 2
        hsrp_enabled = False
        etherchannel_enabled = True
        reason_code = "REDUNDANCY_DUAL_UPLINK_ENABLED"
    else:  # "none"
        core_count = 1
        firewall_count = 1
        dist_pair = False
        uplinks_per_access = 1
        hsrp_enabled = False
        etherchannel_enabled = False
        reason_code = "REDUNDANCY_NONE_SINGLE_UPLINK"

    decision = Decision(
        stage="redundancy",
        choice=level,
        reason_code=reason_code,
        params={
            "level": level,
            "core_count": core_count,
            "firewall_count": firewall_count,
            "uplinks_per_access": uplinks_per_access,
            "hsrp_enabled": hsrp_enabled,
            "etherchannel_enabled": etherchannel_enabled,
        },
    )

    return RedundancyPlan(
        level=level,
        core_count=core_count,
        firewall_count=firewall_count,
        dist_pair=dist_pair,
        uplinks_per_access=uplinks_per_access,
        hsrp_enabled=hsrp_enabled,
        etherchannel_enabled=etherchannel_enabled,
        decision=decision,
    )


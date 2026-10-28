"""
requirements.py — Pydantic models for user requirements input.
Spec Section 5.1.
"""
from typing import Literal
from pydantic import BaseModel, Field

DeptType = Literal[
    "office",
    "engineering",
    "finance",
    "hr",
    "management",
    "reception",
    "lab",
    "media",
    "datacenter_ops",
    "support",
]

SecurityLevel = Literal["low", "medium", "high", "critical"]

OrgType = Literal[
    "school",
    "hospital",
    "it_company",
    "corporate",
    "government",
    "other",
]

RedundancyLevel = Literal["none", "dual_uplink", "full_ha"]


class Department(BaseModel):
    name: str
    users: int
    floor: int
    dept_type: DeptType
    security_level: SecurityLevel
    needs_guest_access: bool = False
    wired_printers: int = 0
    notes: str = ""


class ServerSpec(BaseModel):
    count: int
    public_facing: int = 0


class RequirementsInput(BaseModel):
    org_name: str
    org_type: OrgType
    floors: int
    departments: list[Department]
    servers: ServerSpec
    wifi_enabled: bool = True
    wifi_user_ratio: float = 0.6
    guest_wifi: bool = True
    remote_access_vpn: bool = True
    internet_bandwidth_mbps: int = 200
    redundancy: RedundancyLevel = "none"
    growth_percent: float = 30.0
    growth_years: int = 3
    budget: float | None = None
    base_network: str = "10.0.0.0/16"


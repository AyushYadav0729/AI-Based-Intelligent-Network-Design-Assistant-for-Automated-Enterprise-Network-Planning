"""
design.py — Pydantic models for the generated design results.
Spec Section 5.2 and Section 10.
"""
from typing import Any, Literal
from pydantic import BaseModel, Field
from app.schemas.validation import ValidationIssue

DeviceRole = Literal[
    "core",
    "distribution",
    "access",
    "firewall",
    "router",
    "wlc",
    "ap",
    "server_switch",
]

VariantName = Literal["budget", "balanced", "high_performance"]


class Vlan(BaseModel):
    vlan_id: int
    name: str
    purpose: str
    dept: str | None = None


class Subnet(BaseModel):
    vlan_id: int | None = None
    name: str
    network: str
    prefix: int
    mask: str
    gateway: str
    usable_hosts: int
    required_hosts: int
    utilization_pct: float
    first_host: str
    last_host: str
    broadcast: str
    hsrp: dict[str, str] | None = None


class DeviceItem(BaseModel):
    role: DeviceRole
    catalog_id: str
    model: str
    quantity: int
    unit_price: float
    total_price: float
    location: str


class Decision(BaseModel):
    stage: str
    choice: str
    reason_code: str
    params: dict[str, Any]
    explanation: str | None = None


class DesignResult(BaseModel):
    variant: VariantName
    topology: str
    vlans: list[Vlan]
    subnets: list[Subnet]
    p2p_links: list[Subnet] = Field(default_factory=list)
    devices: list[DeviceItem]
    routing: dict[str, Any]
    security: dict[str, Any]
    bandwidth: dict[str, Any]
    cost: dict[str, Any]
    capacity: dict[str, Any]
    graph: dict[str, Any]
    decisions: list[Decision]
    validation: list[ValidationIssue]


class DesignGenerateResponse(BaseModel):
    variants: dict[VariantName, DesignResult]
    comparison: list[dict[str, Any]]
    comparison_summary: str
    explanation_source: Literal["llm", "template"] = "template"


"""
devices.py — Deterministic device selection, port sizing, and quantities from catalog.
Spec Section 6.6.
"""
from dataclasses import dataclass
import math
from typing import Literal

from app.config import (
    CLIENTS_PER_AP,
    WLC_THRESHOLD_APS,
    PORT_HEADROOM_BALANCED,
    ACCESS_SWITCH_SPARE_PORTS,
    PORTS_24,
    PORTS_48,
)
from app.schemas.requirements import RequirementsInput
from app.schemas.design import DeviceItem, Decision
from app.schemas.catalog import DeviceCatalog, CatalogDevice
from app.catalog.loader import get_catalog, get_devices_by_role
from app.engine.growth import GrowthProjection
from app.engine.redundancy import RedundancyPlan


@dataclass(frozen=True)
class DeviceSizingResult:
    items: list[DeviceItem]
    total_access_switches: int
    total_aps: int
    wlc_required: bool
    decisions: list[Decision]


def _pick_device(
    role: str,
    tier: str,
    catalog: DeviceCatalog,
    poe_required: bool = False,
    min_ports: int = 0,
    min_throughput_gbps: float = 0.0,
) -> CatalogDevice:
    """Selects the best matching catalog device for a role, tier, and constraints."""
    candidates = get_devices_by_role(role, catalog)
    if not candidates:
        raise ValueError(f"No catalog devices found for role: {role}")

    # Filter by PoE if required
    if poe_required:
        poe_matches = [d for d in candidates if d.poe]
        if poe_matches:
            candidates = poe_matches

    # Filter by min ports if specified
    if min_ports > 0:
        port_matches = [d for d in candidates if d.ports.access >= min_ports]
        if port_matches:
            candidates = port_matches

    # Filter by throughput if specified
    if min_throughput_gbps > 0:
        thru_matches = [d for d in candidates if d.throughput_gbps >= min_throughput_gbps]
        if thru_matches:
            candidates = thru_matches

    # Prefer requested tier, fallback to any available
    tier_matches = [d for d in candidates if d.tier == tier]
    if tier_matches:
        return tier_matches[0]

    # Fallback to cheapest candidate
    return sorted(candidates, key=lambda d: d.price)[0]


def size_devices(
    req: RequirementsInput,
    growth: GrowthProjection,
    topology: str,
    redundancy: RedundancyPlan,
    tier: Literal["low", "mid", "high"] = "mid",
    port_headroom: float = PORT_HEADROOM_BALANCED,
    catalog: DeviceCatalog | None = None,
) -> DeviceSizingResult:
    """
    Sizes and selects all network hardware from catalog.
    Spec Section 6.6.
    """
    cat = catalog or get_catalog()
    items: list[DeviceItem] = []
    decisions: list[Decision] = []

    # 1. Access Points (per floor)
    floor_aps: dict[int, int] = {}
    if req.wifi_enabled:
        for fl in range(req.floors):
            fl_users = sum(
                d.planned_users for d in growth.departments if min(d.floor, req.floors - 1) == fl
            )
            fl_ap_count = max(1, math.ceil(fl_users * req.wifi_user_ratio / CLIENTS_PER_AP))
            floor_aps[fl] = fl_ap_count

        total_aps = sum(floor_aps.values())
        ap_dev = _pick_device("ap", tier, cat, poe_required=True)
        items.append(
            DeviceItem(
                role="ap",
                catalog_id=ap_dev.id,
                model=ap_dev.model,
                quantity=total_aps,
                unit_price=ap_dev.price,
                total_price=round(ap_dev.price * total_aps, 2),
                location=f"Floors 0–{req.floors - 1} Ceilings",
            )
        )
    else:
        total_aps = 0

    # 2. Wireless LAN Controller (if total APs > threshold)
    wlc_required = total_aps > WLC_THRESHOLD_APS
    if wlc_required:
        wlc_dev = _pick_device("wlc", tier, cat)
        items.append(
            DeviceItem(
                role="wlc",
                catalog_id=wlc_dev.id,
                model=wlc_dev.model,
                quantity=1,
                unit_price=wlc_dev.price,
                total_price=wlc_dev.price,
                location="MDF - Central Rack",
            )
        )

    # 3. Access Switches (per floor)
    total_access_switches = 0
    for fl in range(req.floors):
        fl_users = sum(
            d.planned_users for d in growth.departments if min(d.floor, req.floors - 1) == fl
        )
        fl_printers = sum(
            d.wired_printers for d in growth.departments if min(d.floor, req.floors - 1) == fl
        )
        fl_ap = floor_aps.get(fl, 0)
        ports_needed = fl_users + fl_printers + fl_ap + ACCESS_SWITCH_SPARE_PORTS

        switch_size = PORTS_48 if ports_needed > PORTS_24 else PORTS_24
        effective_capacity = switch_size * (1.0 - port_headroom)
        fl_switches = max(1, math.ceil(ports_needed / effective_capacity))
        total_access_switches += fl_switches

        acc_dev = _pick_device(
            role="access",
            tier=tier,
            catalog=cat,
            poe_required=(fl_ap > 0),
            min_ports=switch_size,
        )

        items.append(
            DeviceItem(
                role="access",
                catalog_id=acc_dev.id,
                model=acc_dev.model,
                quantity=fl_switches,
                unit_price=acc_dev.price,
                total_price=round(acc_dev.price * fl_switches, 2),
                location=f"Floor {fl} IDF",
            )
        )

    # 4. Distribution Switches (for three-tier topology)
    if topology == "three_tier":
        dist_blocks = max(1, math.ceil(req.floors / 2))
        dist_count = dist_blocks * (2 if redundancy.dist_pair else 1)
        dist_dev = _pick_device("distribution", tier, cat)
        items.append(
            DeviceItem(
                role="distribution",
                catalog_id=dist_dev.id,
                model=dist_dev.model,
                quantity=dist_count,
                unit_price=dist_dev.price,
                total_price=round(dist_dev.price * dist_count, 2),
                location="Building Distribution IDF",
            )
        )

    # 5. Core Switches
    core_dev = _pick_device("core", tier, cat)
    items.append(
        DeviceItem(
            role="core",
            catalog_id=core_dev.id,
            model=core_dev.model,
            quantity=redundancy.core_count,
            unit_price=core_dev.price,
            total_price=round(core_dev.price * redundancy.core_count, 2),
            location="MDF - Core Rack",
        )
    )

    # 6. Server Switch (ToR for server VLAN)
    if req.servers.count > 0:
        srv_qty = 2 if (redundancy.level == "full_ha" or tier == "high") else 1
        srv_dev = _pick_device("server_switch", tier, cat)
        items.append(
            DeviceItem(
                role="server_switch",
                catalog_id=srv_dev.id,
                model=srv_dev.model,
                quantity=srv_qty,
                unit_price=srv_dev.price,
                total_price=round(srv_dev.price * srv_qty, 2),
                location="Server Room / Datacenter Rack",
            )
        )

    # 7. Perimeter Firewall
    fw_dev = _pick_device(
        role="firewall",
        tier=tier,
        catalog=cat,
        min_throughput_gbps=req.internet_bandwidth_mbps / 1000.0,
    )
    items.append(
        DeviceItem(
            role="firewall",
            catalog_id=fw_dev.id,
            model=fw_dev.model,
            quantity=redundancy.firewall_count,
            unit_price=fw_dev.price,
            total_price=round(fw_dev.price * redundancy.firewall_count, 2),
            location="MDF - Edge Security Rack",
        )
    )

    # 8. Edge Router (for Star topology or Edge WAN termination)
    if topology == "star":
        rtr_dev = _pick_device(
            role="router",
            tier=tier,
            catalog=cat,
            min_throughput_gbps=req.internet_bandwidth_mbps / 1000.0,
        )
        items.append(
            DeviceItem(
                role="router",
                catalog_id=rtr_dev.id,
                model=rtr_dev.model,
                quantity=1,
                unit_price=rtr_dev.price,
                total_price=rtr_dev.price,
                location="MDF - WAN Demarc",
            )
        )

    decisions.append(
        Decision(
            stage="devices",
            choice=f"{len(items)} device types selected",
            reason_code="DEVICE_SELECTION_CATALOG_MATCHED",
            params={
                "tier": tier,
                "port_headroom": port_headroom,
                "total_access_switches": total_access_switches,
                "total_aps": total_aps,
                "wlc_required": wlc_required,
            },
        )
    )

    return DeviceSizingResult(
        items=items,
        total_access_switches=total_access_switches,
        total_aps=total_aps,
        wlc_required=wlc_required,
        decisions=decisions,
    )


"""
vlans.py — Generates the VLAN plan based on requirements and departments.
Spec Section 6.4.
"""
import re
from app.schemas.requirements import RequirementsInput
from app.schemas.design import Vlan


def clean_vlan_name(raw_name: str) -> str:
    """Converts a department name to a clean Cisco-compatible VLAN name."""
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", raw_name).strip("_").upper()
    return cleaned or "DEPT"


def generate_vlan_plan(req: RequirementsInput) -> list[Vlan]:
    """Generates the deterministic VLAN plan for the campus network."""
    vlans: list[Vlan] = []

    # 1. Management VLAN (always present)
    vlans.append(
        Vlan(
            vlan_id=10,
            name="MGMT",
            purpose="Network device management and monitoring",
            dept=None,
        )
    )

    # 2. Internal Servers VLAN (always present)
    vlans.append(
        Vlan(
            vlan_id=20,
            name="SERVERS",
            purpose="Internal enterprise servers",
            dept=None,
        )
    )

    # 3. DMZ VLAN (only if public-facing servers exist)
    if req.servers.public_facing > 0:
        vlans.append(
            Vlan(
                vlan_id=30,
                name="DMZ",
                purpose="Demilitarized Zone for public-facing servers",
                dept=None,
            )
        )

    # 4. Guest VLAN (if guest Wi-Fi or any department needs guest access)
    needs_guest = req.guest_wifi or any(d.needs_guest_access for d in req.departments)
    if needs_guest:
        vlans.append(
            Vlan(
                vlan_id=40,
                name="GUEST",
                purpose="Isolated guest access network",
                dept=None,
            )
        )

    # 5. Corporate Wi-Fi VLAN (if Wi-Fi enabled)
    if req.wifi_enabled:
        vlans.append(
            Vlan(
                vlan_id=50,
                name="WIFI-CORP",
                purpose="Corporate wireless client network",
                dept=None,
            )
        )

    # 6. Department VLANs (100, 110, 120, ...)
    for idx, dept in enumerate(req.departments):
        vlan_id = 100 + (10 * idx)
        vlan_name = clean_vlan_name(dept.name)
        vlans.append(
            Vlan(
                vlan_id=vlan_id,
                name=vlan_name,
                purpose=f"Wired network for department {dept.name}",
                dept=dept.name,
            )
        )

    # 7. Native / Blackhole VLAN (always present for unused ports & trunk native)
    vlans.append(
        Vlan(
            vlan_id=999,
            name="NATIVE_BLACKHOLE",
            purpose="Native VLAN and unused ports parking",
            dept=None,
        )
    )

    return vlans


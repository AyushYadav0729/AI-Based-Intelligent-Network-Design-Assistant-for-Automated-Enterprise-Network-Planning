"""
cli_config.py — Cisco IOS-style CLI configuration generator.
Spec Section 12.1.

Generates per-device sample configurations using Jinja2 templates.
Returns a dict mapping filename → config text, which the caller can ZIP.

NOTE: All output is labeled as 'sample — review before deployment'.
"""
from __future__ import annotations

import ipaddress
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from app.schemas.design import DesignResult, Subnet, Vlan

# ── Template directory ──────────────────────────────────────────────────────
_TEMPLATES_DIR = Path(__file__).parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
)

# Register a helper accessible inside templates
def _wildcard_from_prefix(prefix: int) -> str:
    """Convert CIDR prefix length to wildcard mask used in OSPF network statements."""
    net = ipaddress.IPv4Network(f"0.0.0.0/{prefix}")
    # wildcard = inverted subnet mask
    mask_int = int(net.netmask)
    wild_int = 0xFFFFFFFF ^ mask_int
    return str(ipaddress.IPv4Address(wild_int))

_env.globals["ospf_wildcard_from_prefix"] = _wildcard_from_prefix


# ── Internal helpers ─────────────────────────────────────────────────────────

def _mgmt_subnet_from_subnets(subnets: list[Subnet]) -> str:
    """Return the management subnet network string (e.g. '10.0.8.0')."""
    for s in subnets:
        if s.name == "MGMT":
            net = ipaddress.IPv4Network(f"{s.network}/{s.prefix}", strict=False)
            return str(net.network_address)
    # Fallback: use the smallest subnet's network
    if subnets:
        return subnets[-1].network
    return "10.0.0.0"


def _mgmt_gateway(subnets: list[Subnet]) -> str:
    for s in subnets:
        if s.name == "MGMT":
            return s.gateway
    if subnets:
        return subnets[0].gateway
    return "10.0.0.1"


def _acl_entries_from_matrix(
    acl_matrix: dict[str, dict[str, str]],
    vlans: list[Vlan],
) -> list[dict]:
    """
    Convert the acl_matrix into per-VLAN ACL entries for the core switch template.
    Each entry: {vlan_id, rules: [str]}
    """
    # Build name -> vlan_id mapping
    name_to_id: dict[str, int] = {v.name: v.vlan_id for v in vlans}
    entries = []

    for src_name, destinations in acl_matrix.items():
        vlan_id = name_to_id.get(src_name, 0)
        rules: list[str] = []
        for dst_name, action in destinations.items():
            if src_name == dst_name:
                continue  # Intra-VLAN always permitted at switch level
            dst_id = name_to_id.get(dst_name, 0)
            if action == "deny":
                rules.append(f"deny   ip any 10.0.{dst_id}.0 0.0.255.255  ! to VLAN{dst_id} ({dst_name})")
            elif action == "permit":
                rules.append(f"permit ip any any  ! to VLAN{dst_id} ({dst_name})")
            else:
                # limited — permit specific well-known ports
                rules.append(f"permit tcp any any eq 80   ! HTTP to {dst_name}")
                rules.append(f"permit tcp any any eq 443  ! HTTPS to {dst_name}")
                rules.append(f"permit tcp any any eq 22   ! SSH  to {dst_name}")
                rules.append(f"deny   ip any any log  ! default deny")
        if rules:
            entries.append({"vlan_id": vlan_id, "rules": rules})

    return entries


def _dept_port_ranges(
    design: DesignResult,
    floor_num: int,
    vlans: list[Vlan],
    dept_policies: list[dict],
) -> list[dict]:
    """
    Build per-department port range assignments for an access switch on a given floor.
    Returns list of {dept_name, vlan_id, iface_range, dot1x}.
    """
    name_to_id: dict[str, int] = {v.name: v.dept for v in vlans if v.dept}
    # Build dept name -> vlan_id (dept VLANs start at 100)
    dept_vlans: dict[str, int] = {}
    for v in vlans:
        if v.vlan_id >= 100 and v.dept:
            dept_vlans[v.dept] = v.vlan_id

    dot1x_depts = {p["dept_name"] for p in dept_policies if p.get("dot1x_enabled")}

    ranges = []
    port_start = 1
    for dept_name, vlan_id in dept_vlans.items():
        # Assign 8 ports per department (simplified; in practice calculated from user count)
        port_end = port_start + 7
        ranges.append({
            "dept_name": dept_name,
            "vlan_id": vlan_id,
            "iface_range": f"GigabitEthernet0/{port_start}-{port_end}",
            "dot1x": dept_name in dot1x_depts,
        })
        port_start = port_end + 1

    return ranges


# ── Public API ───────────────────────────────────────────────────────────────

def generate_cli_configs(design: DesignResult) -> dict[str, str]:
    """
    Generate all CLI configuration files for a given DesignResult.

    Returns a mapping of filename → config text (UTF-8 string).
    The caller is responsible for creating a ZIP archive from this mapping.
    """
    configs: dict[str, str] = {}
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    variant = design.variant

    subnets = design.subnets
    vlans = design.vlans
    security = design.security
    dept_policies: list[dict] = security.get("dept_policies", [])
    acl_matrix: dict[str, dict[str, str]] = security.get("acl_matrix", {})

    mgmt_sub = _mgmt_subnet_from_subnets(subnets)
    mgmt_gw = _mgmt_gateway(subnets)
    acl_entries = _acl_entries_from_matrix(acl_matrix, vlans)

    # ── Determine routing protocol ───────────────────────────────────────────
    routing_protocol = design.routing.get("protocol", "OSPF")
    ospf_router_id_base = 1  # Core-1 gets .1, Core-2 gets .2

    # ── Filter subnets to user-facing ones (exclude P2P and None-VLAN) ──────
    user_subnets = [s for s in subnets if s.vlan_id is not None]

    # ── Core / Collapsed-core switch config ──────────────────────────────────
    core_template = _env.get_template("core_switch.j2")

    core_devices = [d for d in design.devices if d.role in ("core", "distribution")]
    core_count = sum(d.quantity for d in core_devices)

    for i in range(max(1, core_count)):
        hostname = f"CORE-SW-{i + 1}"
        ospf_rid = f"1.1.1.{i + 1}"
        # Uplink ports: Gi1/0/1..N toward access/distribution
        uplink_count = min(8, max(2, len(subnets)))

        rendered = core_template.render(
            hostname=hostname,
            variant=variant.upper(),
            generated_at=now,
            vlans=vlans,
            subnets=user_subnets,
            mgmt_subnet=mgmt_sub,
            mgmt_gateway=mgmt_gw,
            routing_protocol=routing_protocol,
            ospf_router_id=ospf_rid,
            uplink_port_count=uplink_count,
            uplink_iface_prefix="GigabitEthernet1/0/",
            etherchannel=(design.routing.get("inter_vlan_method") == "SVI" and i < core_count - 1),
            acl_entries=acl_entries,
        )
        configs[f"{hostname}.txt"] = rendered

    # ── Access switches — one per floor ──────────────────────────────────────
    access_template = _env.get_template("access_switch.j2")

    # Figure out how many access switches and on which floors
    access_devices = [d for d in design.devices if d.role == "access"]
    floors = design.routing.get("passive_interfaces", [])  # not ideal but gives us context
    num_floors = max(1, len({d.location.split("F")[1][0] if "F" in d.location else "1"
                              for d in access_devices}) if access_devices else 1)

    total_access = sum(d.quantity for d in access_devices)
    per_floor = max(1, math.ceil(total_access / num_floors))

    # Find a management subnet IP range to assign to access switches
    mgmt_subnet_obj = next((s for s in subnets if s.name == "MGMT"), None)
    mgmt_host_base = 10  # start assigning mgmt IPs from .10

    for floor_idx in range(num_floors):
        for sw_idx in range(per_floor):
            sw_num = floor_idx * per_floor + sw_idx + 1
            hostname = f"ACC-SW-F{floor_idx + 1}-{sw_idx + 1}"

            if mgmt_subnet_obj:
                mgmt_ip = mgmt_subnet_obj.first_host  # simplified; real: assign sequential IPs
                mgmt_mask = mgmt_subnet_obj.mask
            else:
                mgmt_ip = "10.0.0.10"
                mgmt_mask = "255.255.255.0"

            dept_ranges = _dept_port_ranges(design, floor_idx, vlans, dept_policies)

            # Calculate unused port range (after all dept ports)
            used_ports = sum(8 for _ in dept_ranges)  # 8 ports per dept (simplified)
            unused_start = used_ports + 1
            unused_end = 48  # standard 48-port switch

            uplink_ports = [
                {
                    "iface": f"GigabitEthernet0/49",
                    "target": f"CORE-SW-1",
                    "etherchannel": False,
                    "channel_group": 1,
                }
            ]
            if design.routing.get("inter_vlan_method") and sw_num <= 2:
                # dual uplink for redundancy
                uplink_ports.append({
                    "iface": "GigabitEthernet0/50",
                    "target": "CORE-SW-2",
                    "etherchannel": False,
                    "channel_group": 2,
                })

            rendered = access_template.render(
                hostname=hostname,
                floor=floor_idx + 1,
                variant=variant.upper(),
                generated_at=now,
                vlans=vlans,
                mgmt_ip=mgmt_ip,
                mgmt_mask=mgmt_mask,
                mgmt_subnet=mgmt_sub,
                mgmt_gateway=mgmt_gw,
                dept_port_ranges=dept_ranges,
                uplink_ports=uplink_ports,
                unused_iface_range=f"GigabitEthernet0/{unused_start}-{unused_end}"
                    if unused_start <= unused_end else "GigabitEthernet0/48",
            )
            configs[f"{hostname}.txt"] = rendered

    # ── Firewall / Edge router config ─────────────────────────────────────────
    fw_template = _env.get_template("firewall.j2")

    fw_devices = [d for d in design.devices if d.role == "firewall"]
    fw_count = max(1, sum(d.quantity for d in fw_devices))

    # Find inside and DMZ subnet info
    inside_subnet = user_subnets[0] if user_subnets else None
    dmz_subnet = next((s for s in subnets if s.name == "DMZ"), None)

    inside_net = ipaddress.IPv4Network(
        f"{inside_subnet.network}/{inside_subnet.prefix}", strict=False
    ) if inside_subnet else ipaddress.IPv4Network("10.0.0.0/16")

    dmz_net = ipaddress.IPv4Network(
        f"{dmz_subnet.network}/{dmz_subnet.prefix}", strict=False
    ) if dmz_subnet else None

    for i in range(min(fw_count, 2)):  # max 2 firewall configs (HA pair)
        hostname = f"FW-EDGE-{i + 1}"

        fw_ctx = {
            "hostname": hostname,
            "variant": variant.upper(),
            "generated_at": now,
            "dmz_enabled": security.get("dmz_enabled", False),
            "vpn_enabled": security.get("remote_access_vpn", False),
            "inside_ip": str(list(inside_net.hosts())[0]),
            "inside_mask": str(inside_net.netmask),
            "inside_network": str(inside_net.network_address),
            "inside_netmask": str(inside_net.netmask),
            "mgmt_gateway": mgmt_gw,
            "mgmt_subnet": mgmt_sub,
        }

        if dmz_net:
            fw_ctx.update({
                "dmz_gateway": str(list(dmz_net.hosts())[0]),
                "dmz_mask": str(dmz_net.netmask),
                "dmz_network": str(dmz_net.network_address),
                "dmz_netmask": str(dmz_net.netmask),
                "dmz_first_host_prefix": ".".join(str(dmz_net.network_address).split(".")[:3]) + ".",
                "dmz_server_count": min(3, security.get("dmz_server_count", 1)),
            })
        else:
            fw_ctx.update({
                "dmz_gateway": "10.0.30.1",
                "dmz_mask": "255.255.255.0",
                "dmz_network": "10.0.30.0",
                "dmz_netmask": "255.255.255.0",
                "dmz_first_host_prefix": "10.0.30.",
                "dmz_server_count": 0,
            })

        rendered = fw_template.render(**fw_ctx)
        configs[f"{hostname}.txt"] = rendered

    # ── README inside the ZIP ─────────────────────────────────────────────────
    configs["README.txt"] = _build_readme(variant, now, list(configs.keys()))

    return configs


def _build_readme(variant: str, generated_at: str, filenames: list[str]) -> str:
    names_list = "\n".join(f"  - {f}" for f in filenames if f != "README.txt")
    return f"""\
AI Network Design Assistant — CLI Configuration Export
======================================================
Variant      : {variant.upper()}
Generated    : {generated_at}

IMPORTANT NOTICE
----------------
These configurations are SAMPLES generated from a deterministic design model.
They illustrate the intended architecture and must be reviewed, tested, and
adapted by a qualified network engineer before deployment.

All sensitive values (passwords, PSKs, RADIUS secrets) are placeholders
marked [CHANGE_ME] or [AUTH_PASS]. Replace them before use.

Files Included
--------------
{names_list}

How to Use
----------
1. Review each file and adapt interface numbers to match your physical hardware.
2. Replace all placeholder values.
3. Apply in a lab / Packet Tracer environment before production.
4. Use 'copy tftp running-config' or paste directly in privileged EXEC mode.

Assumptions
-----------
- Cisco IOS / IOS-XE syntax (not NX-OS).
- IPv4 only; no IPv6 configuration is generated.
- OSPF Area 0 used for enterprise designs; static routes for small topologies.
- Port numbering is illustrative; verify against physical switch port counts.
"""

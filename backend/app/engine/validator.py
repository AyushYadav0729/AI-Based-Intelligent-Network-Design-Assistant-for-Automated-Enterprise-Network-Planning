"""
validator.py — Rule-based deterministic validator for network designs.
Spec Section 7.
Returns a list of ValidationIssue items covering addressing, VLANs, links, ports, redundancy, security, and cost.
"""
import ipaddress
from typing import Any

from app.config import (
    SUBNET_LOW_HEADROOM_PCT,
    OVERSUB_ACCESS_TO_DIST_MAX,
    OVERSUB_DIST_TO_CORE_MAX,
    ACCESS_SWITCH_SPARE_PORTS,
)
from app.schemas.requirements import RequirementsInput
from app.schemas.design import DesignResult, Vlan, Subnet, DeviceItem
from app.schemas.validation import ValidationIssue

# Reserved Cisco VLAN IDs
RESERVED_VLAN_IDS = {0, 1, 1002, 1003, 1004, 1005}


def validate_design(
    design: DesignResult,
    req: RequirementsInput,
) -> list[ValidationIssue]:
    """
    Executes all rule-based deterministic checks specified in Section 7.
    """
    issues: list[ValidationIssue] = []

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Addressing Checks
    # ─────────────────────────────────────────────────────────────────────────
    all_subnets = design.subnets + design.p2p_links
    subnet_nets: list[tuple[Subnet, ipaddress.IPv4Network]] = []

    for s in all_subnets:
        try:
            net = ipaddress.IPv4Network(f"{s.network}/{s.prefix}", strict=True)
            subnet_nets.append((s, net))
        except ValueError as e:
            issues.append(
                ValidationIssue(
                    code="ADDR_GATEWAY_INVALID",
                    severity="error",
                    message=f"Invalid network definition {s.network}/{s.prefix}: {e}",
                    related=[s.name],
                )
            )

    # 1.1 ADDR_OVERLAP
    for i in range(len(subnet_nets)):
        s1, net1 = subnet_nets[i]
        for j in range(i + 1, len(subnet_nets)):
            s2, net2 = subnet_nets[j]
            if net1.overlaps(net2):
                issues.append(
                    ValidationIssue(
                        code="ADDR_OVERLAP",
                        severity="error",
                        message=f"Subnets overlap: {s1.name} ({net1}) and {s2.name} ({net2})",
                        related=[s1.name, s2.name],
                    )
                )

    # 1.2 ADDR_OUTSIDE_PRIVATE
    for s, net in subnet_nets:
        if not net.is_private:
            issues.append(
                ValidationIssue(
                    code="ADDR_OUTSIDE_PRIVATE",
                    severity="error",
                    message=f"Subnet {s.name} ({net}) is not in RFC1918 private address space",
                    related=[s.name],
                )
            )

    # 1.3 ADDR_HOSTS_INSUFFICIENT & 1.4 ADDR_LOW_HEADROOM & 1.5 ADDR_GATEWAY_INVALID
    for s, net in subnet_nets:
        # Host capacity
        if s.usable_hosts < s.required_hosts:
            issues.append(
                ValidationIssue(
                    code="ADDR_HOSTS_INSUFFICIENT",
                    severity="error",
                    message=(
                        f"Subnet {s.name} usable hosts ({s.usable_hosts}) < "
                        f"required hosts ({s.required_hosts})"
                    ),
                    related=[s.name],
                )
            )

        # Headroom warning (exclude P2P links)
        if s.vlan_id is not None:
            if s.utilization_pct > (SUBNET_LOW_HEADROOM_PCT * 100.0):
                issues.append(
                    ValidationIssue(
                        code="ADDR_LOW_HEADROOM",
                        severity="warning",
                        message=(
                            f"Subnet {s.name} utilization is {s.utilization_pct}% "
                            f"(exceeds {int(SUBNET_LOW_HEADROOM_PCT * 100)}% warning threshold)"
                        ),
                        related=[s.name],
                    )
                )

        # Gateway validity
        try:
            gw_ip = ipaddress.IPv4Address(s.gateway)
            if gw_ip not in net:
                issues.append(
                    ValidationIssue(
                        code="ADDR_GATEWAY_INVALID",
                        severity="error",
                        message=f"Gateway {s.gateway} is outside subnet {net}",
                        related=[s.name],
                    )
                )
            elif gw_ip == net.network_address or gw_ip == net.broadcast_address:
                issues.append(
                    ValidationIssue(
                        code="ADDR_GATEWAY_INVALID",
                        severity="error",
                        message=f"Gateway {s.gateway} cannot equal network or broadcast address in {net}",
                        related=[s.name],
                    )
                )
        except ValueError:
            issues.append(
                ValidationIssue(
                    code="ADDR_GATEWAY_INVALID",
                    severity="error",
                    message=f"Gateway '{s.gateway}' is not a valid IPv4 address in subnet {s.name}",
                    related=[s.name],
                )
            )

    # ─────────────────────────────────────────────────────────────────────────
    # 2. VLAN Checks
    # ─────────────────────────────────────────────────────────────────────────
    vlan_ids_seen: set[int] = set()
    vlan_names_seen: set[str] = set()

    for v in design.vlans:
        # 2.1 VLAN_DUPLICATE_ID
        if v.vlan_id in vlan_ids_seen:
            issues.append(
                ValidationIssue(
                    code="VLAN_DUPLICATE_ID",
                    severity="error",
                    message=f"Duplicate VLAN ID detected: {v.vlan_id}",
                    related=[v.name],
                )
            )
        vlan_ids_seen.add(v.vlan_id)

        # 2.2 VLAN_DUPLICATE_NAME
        name_lower = v.name.lower()
        if name_lower in vlan_names_seen:
            issues.append(
                ValidationIssue(
                    code="VLAN_DUPLICATE_NAME",
                    severity="warning",
                    message=f"Duplicate VLAN name detected: {v.name}",
                    related=[v.name],
                )
            )
        vlan_names_seen.add(name_lower)

        # 2.3 VLAN_RESERVED_ID
        if v.vlan_id in RESERVED_VLAN_IDS or v.vlan_id < 1 or v.vlan_id > 4094:
            issues.append(
                ValidationIssue(
                    code="VLAN_RESERVED_ID",
                    severity="error",
                    message=f"VLAN ID {v.vlan_id} is reserved or outside valid range (1–4094)",
                    related=[v.name],
                )
            )

    # 2.4 VLAN_NO_SUBNET
    # Check that every routed VLAN has an IP subnet
    subnet_vlan_ids = {s.vlan_id for s in design.subnets if s.vlan_id is not None}
    for v in design.vlans:
        # VLAN 999 is intentionally blackhole/unrouted
        if v.vlan_id == 999:
            continue
        if v.vlan_id not in subnet_vlan_ids:
            issues.append(
                ValidationIssue(
                    code="VLAN_NO_SUBNET",
                    severity="error",
                    message=f"VLAN {v.vlan_id} ({v.name}) has no associated IP subnet",
                    related=[v.name],
                )
            )

    # Check reverse: every subnet with vlan_id has a declared VLAN
    all_vlan_ids = {v.vlan_id for v in design.vlans}
    for s in design.subnets:
        if s.vlan_id is not None and s.vlan_id not in all_vlan_ids:
            issues.append(
                ValidationIssue(
                    code="VLAN_NO_SUBNET",
                    severity="error",
                    message=f"Subnet {s.name} references non-existent VLAN ID {s.vlan_id}",
                    related=[s.name],
                )
            )

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Link Sizing & Oversubscription Checks
    # ─────────────────────────────────────────────────────────────────────────
    bw_data = design.bandwidth or {}
    links = bw_data.get("links", [])

    for link in links:
        link_name = link.get("link_name", "")
        oversub = link.get("oversubscription_ratio", 1.0)
        util_pct = link.get("utilization_pct", 0.0)

        # 3.1 LINK_OVERSUB_ACCESS
        if "Access" in link_name and oversub > OVERSUB_ACCESS_TO_DIST_MAX:
            issues.append(
                ValidationIssue(
                    code="LINK_OVERSUB_ACCESS",
                    severity="warning",
                    message=(
                        f"Access uplink {link_name} oversubscription is {oversub}:1 "
                        f"(exceeds recommended {int(OVERSUB_ACCESS_TO_DIST_MAX)}:1 limit)"
                    ),
                    related=[link_name],
                )
            )

        # 3.2 LINK_OVERSUB_DIST
        if "Distribution" in link_name and oversub > OVERSUB_DIST_TO_CORE_MAX:
            issues.append(
                ValidationIssue(
                    code="LINK_OVERSUB_DIST",
                    severity="warning",
                    message=(
                        f"Distribution uplink {link_name} oversubscription is {oversub}:1 "
                        f"(exceeds recommended {int(OVERSUB_DIST_TO_CORE_MAX)}:1 limit)"
                    ),
                    related=[link_name],
                )
            )

        # 3.3 LINK_UTIL_HIGH
        if util_pct > 80.0:
            issues.append(
                ValidationIssue(
                    code="LINK_UTIL_HIGH",
                    severity="warning",
                    message=f"Link {link_name} utilization is high at {util_pct}%",
                    related=[link_name],
                )
            )

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Port Sufficiency Check
    # ─────────────────────────────────────────────────────────────────────────
    # 4.1 PORT_INSUFFICIENT
    # Verify each floor's switch access ports accommodate the needed floor ports
    access_devices = [d for d in design.devices if d.role == "access"]
    for fl in range(req.floors):
        fl_users = sum(d.users for d in req.departments if min(d.floor, req.floors - 1) == fl)
        fl_printers = sum(d.wired_printers for d in req.departments if min(d.floor, req.floors - 1) == fl)
        needed_ports = fl_users + fl_printers + ACCESS_SWITCH_SPARE_PORTS

        # Sum switch ports allocated to this floor
        fl_loc_substr = f"Floor {fl}"
        fl_switches = [d for d in access_devices if fl_loc_substr in d.location]
        # In our catalog, standard access switches have 24 or 48 access ports
        total_access_ports = 0
        for sw in fl_switches:
            ports_per_sw = 48 if "48-port" in sw.model else 24
            total_access_ports += ports_per_sw * sw.quantity

        if fl_switches and total_access_ports < needed_ports:
            issues.append(
                ValidationIssue(
                    code="PORT_INSUFFICIENT",
                    severity="error",
                    message=(
                        f"Floor {fl} total switch ports ({total_access_ports}) < "
                        f"required access ports ({needed_ports})"
                    ),
                    related=[f"Floor {fl}"],
                )
            )

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Redundancy & Single Points of Failure
    # ─────────────────────────────────────────────────────────────────────────
    core_count = sum(d.quantity for d in design.devices if d.role == "core")
    fw_count = sum(d.quantity for d in design.devices if d.role == "firewall")

    # 5.1 SPOF_CORE
    if req.redundancy in ["dual_uplink", "full_ha"] and core_count < 2 and design.variant != "budget":
        if req.redundancy == "full_ha":
            issues.append(
                ValidationIssue(
                    code="SPOF_CORE",
                    severity="warning",
                    message="Single core switch present despite full_ha redundancy requirement",
                    related=["Core Switch"],
                )
            )

    # 5.2 SPOF_FIREWALL
    if req.redundancy == "full_ha" and fw_count < 2:
        issues.append(
            ValidationIssue(
                code="SPOF_FIREWALL",
                severity="warning",
                message="Single firewall present under full_ha redundancy",
                related=["Firewall"],
            )
        )

    # ─────────────────────────────────────────────────────────────────────────
    # 6. Security Architecture Checks
    # ─────────────────────────────────────────────────────────────────────────
    sec_data = design.security or {}

    # 6.1 SECURITY_NO_FIREWALL
    if fw_count == 0:
        issues.append(
            ValidationIssue(
                code="SECURITY_NO_FIREWALL",
                severity="error",
                message="No perimeter firewall provisioned in design",
                related=["Security"],
            )
        )

    # 6.2 SECURITY_DMZ_MISSING
    if req.servers.public_facing > 0:
        has_dmz = any(v.name == "DMZ" for v in design.vlans)
        if not has_dmz:
            issues.append(
                ValidationIssue(
                    code="SECURITY_DMZ_MISSING",
                    severity="error",
                    message="Public-facing servers specified but no DMZ VLAN/subnet configured",
                    related=["DMZ", "SERVERS"],
                )
            )

    # 6.3 SECURITY_GUEST_NOT_ISOLATED
    acl_matrix = sec_data.get("acl_matrix", {})
    if "GUEST" in acl_matrix:
        guest_rules = acl_matrix["GUEST"]
        for dst, rule in guest_rules.items():
            if dst != "GUEST" and rule == "permit":
                issues.append(
                    ValidationIssue(
                        code="SECURITY_GUEST_NOT_ISOLATED",
                        severity="error",
                        message=f"Guest VLAN is permitted direct access to internal VLAN '{dst}'",
                        related=["GUEST", dst],
                    )
                )

    # 6.4 SECURITY_HIGH_NO_8021X
    dept_policies = sec_data.get("dept_policies", [])
    for dp in dept_policies:
        if dp.get("security_level") in ["high", "critical"] and not dp.get("dot1x_enabled"):
            issues.append(
                ValidationIssue(
                    code="SECURITY_HIGH_NO_8021X",
                    severity="warning",
                    message=f"Department '{dp.get('dept_name')}' has {dp.get('security_level')} security but 802.1X is disabled",
                    related=[dp.get("dept_name", "")],
                )
            )

    # ─────────────────────────────────────────────────────────────────────────
    # 7. Cost & Budget Check
    # ─────────────────────────────────────────────────────────────────────────
    # 7.1 COST_OVER_BUDGET
    cost_data = design.cost or {}
    total_cost = cost_data.get("total_cost", 0.0)
    if req.budget is not None and total_cost > req.budget:
        issues.append(
            ValidationIssue(
                code="COST_OVER_BUDGET",
                severity="warning",
                message=(
                    f"Total cost (${total_cost:,.2f}) exceeds configured budget "
                    f"(${req.budget:,.2f}) by ${total_cost - req.budget:,.2f}"
                ),
                related=["Cost"],
            )
        )

    # 7.2 CATALOG_NO_MATCH
    if len(design.devices) == 0:
        issues.append(
            ValidationIssue(
                code="CATALOG_NO_MATCH",
                severity="error",
                message="No catalog devices matched design requirements",
                related=["Devices"],
            )
        )

    return issues


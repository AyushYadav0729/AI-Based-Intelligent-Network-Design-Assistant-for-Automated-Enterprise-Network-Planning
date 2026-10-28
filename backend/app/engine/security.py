"""
security.py — Security architecture, ACL matrix generation, and hardening policies.
Spec Section 6.8.
"""
from dataclasses import dataclass
from typing import Any
from app.schemas.requirements import RequirementsInput
from app.schemas.design import Decision, Vlan


@dataclass(frozen=True)
class DepartmentSecurityPolicy:
    dept_name: str
    security_level: str
    dot1x_enabled: bool
    dhcp_snooping: bool
    dai_enabled: bool
    direct_internet: bool
    logging_enabled: bool
    policies: list[str]


@dataclass(frozen=True)
class SecurityPlan:
    perimeter_firewall: bool
    dmz_enabled: bool
    guest_isolated: bool
    nat_pat_enabled: bool
    remote_access_vpn: bool
    port_security: dict[str, Any]
    mgmt_hardening: dict[str, Any]
    dept_policies: list[DepartmentSecurityPolicy]
    acl_matrix: dict[str, dict[str, str]]
    decisions: list[Decision]

    def to_dict(self) -> dict[str, Any]:
        return {
            "perimeter_firewall": self.perimeter_firewall,
            "dmz_enabled": self.dmz_enabled,
            "guest_isolated": self.guest_isolated,
            "nat_pat_enabled": self.nat_pat_enabled,
            "remote_access_vpn": self.remote_access_vpn,
            "port_security": self.port_security,
            "mgmt_hardening": self.mgmt_hardening,
            "dept_policies": [
                {
                    "dept_name": p.dept_name,
                    "security_level": p.security_level,
                    "dot1x_enabled": p.dot1x_enabled,
                    "dhcp_snooping": p.dhcp_snooping,
                    "dai_enabled": p.dai_enabled,
                    "direct_internet": p.direct_internet,
                    "logging_enabled": p.logging_enabled,
                    "policies": p.policies,
                }
                for p in self.dept_policies
            ],
            "acl_matrix": self.acl_matrix,
        }


def generate_acl_matrix(vlans: list[Vlan]) -> dict[str, dict[str, str]]:
    """
    Constructs the inter-VLAN ACL matrix.
    Rows: source VLAN, Columns: destination VLAN.
    Values: 'permit', 'deny', or 'limited (ports)'
    """
    matrix: dict[str, dict[str, str]] = {}
    vlan_names = [v.name for v in vlans if v.vlan_id != 999]

    for src in vlan_names:
        matrix[src] = {}
        for dst in vlan_names:
            if src == dst:
                matrix[src][dst] = "permit"
            elif src == "GUEST":
                # Guest isolated from all internal VLANs
                matrix[src][dst] = "deny"
            elif src == "DMZ":
                # DMZ isolated from internal corporate network
                matrix[src][dst] = "deny"
            elif src == "MGMT":
                # Management can reach all infrastructure
                matrix[src][dst] = "permit"
            elif dst == "DMZ":
                # Internal to DMZ limited to web/app ports
                matrix[src][dst] = "limited (HTTP/HTTPS)"
            elif dst == "SERVERS":
                # Internal to servers permitted or limited by role
                matrix[src][dst] = "limited (App/DB/File)"
            elif dst == "MGMT":
                # Non-management reaching MGMT is denied
                matrix[src][dst] = "deny"
            else:
                # Inter-department traffic
                matrix[src][dst] = "limited"

    return matrix


def design_security(
    req: RequirementsInput,
    vlans: list[Vlan],
) -> SecurityPlan:
    """
    Designs the comprehensive security architecture and policies.
    Spec Section 6.8.
    """
    dept_policies: list[DepartmentSecurityPolicy] = []

    for dept in req.departments:
        lvl = dept.security_level
        policies: list[str] = ["Standard Outbound Internet ACL", "Basic Port Security (Max 2 MACs)"]
        dot1x = False
        snooping = False
        dai = False
        direct_inet = True
        logging = False

        if lvl in ["medium", "high", "critical"]:
            policies.append("Role-Based Inter-VLAN ACL to Servers")

        if lvl in ["high", "critical"]:
            dot1x = True
            snooping = True
            dai = True
            policies.extend([
                "802.1X Port Authentication (RADIUS)",
                "DHCP Snooping & Dynamic ARP Inspection (DAI)",
            ])

        if lvl == "critical":
            direct_inet = False
            logging = True
            policies.extend([
                "Dedicated VLAN Isolation",
                "Explicit Allow-List ACLs Only (No Direct Internet)",
                "Centralized Syslog Auditing",
            ])

        dept_policies.append(
            DepartmentSecurityPolicy(
                dept_name=dept.name,
                security_level=lvl,
                dot1x_enabled=dot1x,
                dhcp_snooping=snooping,
                dai_enabled=dai,
                direct_internet=direct_inet,
                logging_enabled=logging,
                policies=policies,
            )
        )

    acl_matrix = generate_acl_matrix(vlans)

    port_security = {
        "max_mac_addresses": 2,
        "violation_action": "restrict",
        "aging_type": "inactivity",
        "aging_time_minutes": 10,
        "unused_ports_vlan": 999,
        "unused_ports_status": "shutdown",
    }

    mgmt_hardening = {
        "ssh_version": 2,
        "telnet_disabled": True,
        "vty_acl_applied": True,
        "snmp_version": "v3",
        "aaa_radius_recommended": any(p.dot1x_enabled for p in dept_policies),
    }

    decisions = [
        Decision(
            stage="security",
            choice="Enterprise multi-layer security architecture",
            reason_code="SECURITY_POLICIES_GENERATED",
            params={
                "perimeter_firewall": True,
                "dmz_enabled": req.servers.public_facing > 0,
                "guest_isolated": True,
                "remote_access_vpn": req.remote_access_vpn,
                "dot1x_departments": [p.dept_name for p in dept_policies if p.dot1x_enabled],
            },
        )
    ]

    return SecurityPlan(
        perimeter_firewall=True,
        dmz_enabled=(req.servers.public_facing > 0),
        guest_isolated=True,
        nat_pat_enabled=True,
        remote_access_vpn=req.remote_access_vpn,
        port_security=port_security,
        mgmt_hardening=mgmt_hardening,
        dept_policies=dept_policies,
        acl_matrix=acl_matrix,
        decisions=decisions,
    )


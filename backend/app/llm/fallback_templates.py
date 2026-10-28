"""
fallback_templates.py — Jinja2 template-based explanation fallbacks.
Spec Section 9.3.
Provides deterministic, reliable natural language explanations keyed by machine-readable reason_code.
"""
from jinja2 import Template

TEMPLATES: dict[str, str] = {
    # ── Topology ──
    "TOPO_STAR_SMALL_NETWORK": (
        "A Star topology was selected because the campus accommodates {{ total_planned_users }} planned users "
        "across {{ floors }} floor(s), falling within the star architecture threshold "
        "(≤ {{ max_star_users }} users and ≤ {{ max_star_floors }} floors)."
    ),
    "TOPO_COLLAPSED_CORE_MID_NETWORK": (
        "A Collapsed Core topology was selected because the organization supports {{ total_planned_users }} planned users "
        "across {{ floors }} floor(s) and {{ access_switch_count }} access switches, fitting within the collapsed core boundary "
        "(≤ {{ max_collapsed_users }} users and ≤ {{ max_collapsed_floors }} floors)."
    ),
    "TOPO_THREE_TIER_LARGE_NETWORK": (
        "A Three-Tier hierarchical campus topology (Core, Distribution, Access) was selected because the network scale "
        "({{ total_planned_users }} planned users across {{ floors }} floors) exceeds the collapsed core threshold, "
        "requiring dedicated distribution switches for floor traffic aggregation."
    ),

    # ── Redundancy ──
    "REDUNDANCY_FULL_HA_ENABLED": (
        "Full High Availability architecture is provisioned with redundant dual core switches, active-standby firewall pair, "
        "HSRP first-hop redundancy on every VLAN, and EtherChannel port-channel uplinks."
    ),
    "REDUNDANCY_DUAL_UPLINK_ENABLED": (
        "Dual uplink redundancy is enabled, providing redundant physical connections from each access switch to the core "
        "switch via EtherChannel or Spanning Tree Protocol."
    ),
    "REDUNDANCY_NONE_SINGLE_UPLINK": (
        "A single-core architecture without link aggregation was chosen in accordance with standard availability and budget requirements."
    ),

    # ── Bandwidth ──
    "BANDWIDTH_AGGREGATION_COMPUTED": (
        "Bandwidth demand was aggregated upward with a {{ (target_utilization * 100) | int }}% target link utilization: "
        "total access layer demand is {{ total_access_demand_mbps }} Mbps, server traffic is {{ server_traffic_mbps }} Mbps, "
        "resulting in a core aggregate throughput requirement of {{ core_demand_mbps }} Mbps."
    ),

    # ── Addressing (VLSM) ──
    "ADDR_POOL_EXPANDED": (
        "The base address pool {{ original_pool }} was exhausted by requested subnets and was automatically expanded to "
        "{{ expanded_pool }} to prevent subnet collisions."
    ),

    # ── Devices ──
    "DEVICE_SELECTION_CATALOG_MATCHED": (
        "Hardware devices were selected from the enterprise catalog under the {{ tier }} tier with "
        "{{ (port_headroom * 100) | int }}% switch port headroom, sizing {{ total_access_switches }} access switches "
        "across floors and {{ total_aps }} wireless access points{{ ' with a dedicated Wireless LAN Controller' if wlc_required else '' }}."
    ),

    # ── Routing ──
    "ROUTING_STATIC_SMALL_TOPOLOGY": (
        "Static routing was recommended due to the small scale of the network ({{ subnet_count }} subnets, "
        "{{ l3_device_count }} L3 device), simplifying operations with default route forwarding to the ISP."
    ),
    "ROUTING_OSPF_ENTERPRISE_CONVERGENCE": (
        "OSPF (Open Shortest Path First) Area 0 was recommended for dynamic link-state routing across {{ subnet_count }} subnets "
        "and {{ l3_device_count }} L3 switches, ensuring sub-second convergence, VLSM support, and scalable path selection."
    ),

    # ── Security ──
    "SECURITY_POLICIES_GENERATED": (
        "Multi-tier security policies were generated: perimeter next-gen firewall inspection, "
        "{{ 'DMZ isolation for public servers, ' if dmz_enabled else '' }}guest Wi-Fi segregation, "
        "remote-access VPN, and 802.1X port authentication for high-security departments."
    ),

    # ── Cost ──
    "COST_ESTIMATE_CALCULATED": (
        "Total estimated capital expenditure is ${{ '{:,.2f}'.format(total_cost) }}, comprising hardware (${{ '{:,.2f}'.format(devices_cost) }}), "
        "licensing (${{ '{:,.2f}'.format(licenses_cost) }}), structured cabling (${{ '{:,.2f}'.format(cabling_cost) }}), and rack/UPS infrastructure (${{ '{:,.2f}'.format(rack_ups_cost) }})."
    ),
}

DEFAULT_FALLBACK = "Design decision established in accordance with enterprise LAN architectural guidelines."


def render_template_explanation(reason_code: str, params: dict) -> str:
    """Renders a Jinja2 explanation for a given reason_code and its parameters."""
    tmpl_str = TEMPLATES.get(reason_code)
    if not tmpl_str:
        return DEFAULT_FALLBACK

    try:
        template = Template(tmpl_str)
        return template.render(**params)
    except Exception:
        return DEFAULT_FALLBACK


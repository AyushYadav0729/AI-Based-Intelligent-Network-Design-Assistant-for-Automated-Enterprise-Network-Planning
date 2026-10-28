"""
graph_builder.py — Generates network topology nodes and edges for React Flow and PDF diagrams.
Spec Section 6.12.
"""
from typing import Any
from app.schemas.requirements import RequirementsInput
from app.schemas.design import DeviceItem


def build_network_graph(
    req: RequirementsInput,
    topology: str,
    devices: list[DeviceItem],
    speed_labels: dict[str, str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """
    Constructs top-to-bottom topology graph data with layers:
    'edge' -> 'core' -> 'distribution' -> 'access' -> 'endpoint'.
    """
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    speeds = speed_labels or {}
    core_uplink_speed = speeds.get("core_uplink", "10G")
    dist_uplink_speed = speeds.get("dist_uplink", "10G")
    access_uplink_speed = speeds.get("access_uplink", "1G")

    # 1. Edge Layer: Internet
    nodes.append({
        "id": "internet",
        "type": "internet",
        "label": "Internet / WAN",
        "layer": "edge",
        "floor": None,
        "model": "ISP Demarc",
    })

    # Edge routers & Firewalls
    fw_items = [d for d in devices if d.role == "firewall"]
    fw_count = sum(d.quantity for d in fw_items)
    fw_model = fw_items[0].model if fw_items else "Generic Firewall"

    rtr_items = [d for d in devices if d.role == "router"]
    has_router = len(rtr_items) > 0
    if has_router:
        nodes.append({
            "id": "rtr1",
            "type": "router",
            "label": "Edge Router",
            "layer": "edge",
            "floor": None,
            "model": rtr_items[0].model,
        })
        edges.append({
            "id": "e_inet_rtr",
            "source": "internet",
            "target": "rtr1",
            "speed": f"{req.internet_bandwidth_mbps}M",
            "type": "copper",
            "label": f"{req.internet_bandwidth_mbps} Mbps",
        })
        fw_parent = "rtr1"
    else:
        fw_parent = "internet"

    fw_nodes: list[str] = []
    for i in range(fw_count):
        fw_id = f"fw{i + 1}"
        fw_nodes.append(fw_id)
        nodes.append({
            "id": fw_id,
            "type": "firewall",
            "label": f"Firewall-{i + 1}",
            "layer": "edge",
            "floor": None,
            "model": fw_model,
        })
        edges.append({
            "id": f"e_{fw_parent}_{fw_id}",
            "source": fw_parent,
            "target": fw_id,
            "speed": f"{req.internet_bandwidth_mbps}M",
            "type": "copper",
            "label": f"{req.internet_bandwidth_mbps} Mbps",
        })

    # Firewall HA heartbeat link if pair
    if len(fw_nodes) == 2:
        edges.append({
            "id": "e_fw_ha",
            "source": fw_nodes[0],
            "target": fw_nodes[1],
            "speed": "10G",
            "type": "fiber",
            "label": "HA Heartbeat",
        })

    # 2. Core Layer
    core_items = [d for d in devices if d.role == "core"]
    core_count = sum(d.quantity for d in core_items)
    core_model = core_items[0].model if core_items else "L3 Core Switch"

    core_nodes: list[str] = []
    for i in range(core_count):
        core_id = f"core{i + 1}"
        core_nodes.append(core_id)
        nodes.append({
            "id": core_id,
            "type": "core",
            "label": f"Core Switch {i + 1}" if core_count > 1 else "Core Switch",
            "layer": "core",
            "floor": None,
            "model": core_model,
        })
        # Connect firewalls to core
        for fw_id in fw_nodes:
            edges.append({
                "id": f"e_{fw_id}_{core_id}",
                "source": fw_id,
                "target": core_id,
                "speed": core_uplink_speed,
                "type": "fiber",
                "label": core_uplink_speed,
            })

    # Core peer link / EtherChannel if pair
    if len(core_nodes) == 2:
        edges.append({
            "id": "e_core_peer",
            "source": core_nodes[0],
            "target": core_nodes[1],
            "speed": "40G",
            "type": "fiber",
            "label": "EtherChannel Peer Link",
        })

    # 3. Server Switch & WLC (attached to Core)
    srv_items = [d for d in devices if d.role == "server_switch"]
    if srv_items:
        nodes.append({
            "id": "srv_sw",
            "type": "server_switch",
            "label": "Server ToR Switch",
            "layer": "core",
            "floor": None,
            "model": srv_items[0].model,
        })
        for c_id in core_nodes:
            edges.append({
                "id": f"e_{c_id}_srv_sw",
                "source": c_id,
                "target": "srv_sw",
                "speed": "10G",
                "type": "fiber",
                "label": "10G",
            })

    wlc_items = [d for d in devices if d.role == "wlc"]
    if wlc_items:
        nodes.append({
            "id": "wlc",
            "type": "wlc",
            "label": "Wireless Controller",
            "layer": "core",
            "floor": None,
            "model": wlc_items[0].model,
        })
        edges.append({
            "id": "e_core_wlc",
            "source": core_nodes[0],
            "target": "wlc",
            "speed": "10G",
            "type": "fiber",
            "label": "10G",
        })

    # 4. Distribution Layer (if three_tier)
    dist_nodes: list[str] = []
    if topology == "three_tier":
        dist_items = [d for d in devices if d.role == "distribution"]
        dist_count = sum(d.quantity for d in dist_items)
        dist_model = dist_items[0].model if dist_items else "Distribution Switch"
        for i in range(dist_count):
            d_id = f"dist{i + 1}"
            dist_nodes.append(d_id)
            nodes.append({
                "id": d_id,
                "type": "distribution",
                "label": f"Dist Switch {i + 1}",
                "layer": "distribution",
                "floor": None,
                "model": dist_model,
            })
            # Connect distribution to all core switches
            for c_id in core_nodes:
                edges.append({
                    "id": f"e_{c_id}_{d_id}",
                    "source": c_id,
                    "target": d_id,
                    "speed": dist_uplink_speed,
                    "type": "fiber",
                    "label": dist_uplink_speed,
                })

    # 5. Access Layer (per floor)
    access_items = [d for d in devices if d.role == "access"]
    acc_idx = 1
    for item in access_items:
        for q in range(item.quantity):
            acc_id = f"acc{acc_idx}"
            nodes.append({
                "id": acc_id,
                "type": "access",
                "label": f"Access Sw {acc_idx} ({item.location})",
                "layer": "access",
                "floor": item.location,
                "model": item.model,
            })

            # Uplink targets: distribution if three_tier, else core
            uplink_targets = dist_nodes if topology == "three_tier" else core_nodes
            for target_id in uplink_targets:
                edges.append({
                    "id": f"e_{target_id}_{acc_id}",
                    "source": target_id,
                    "target": acc_id,
                    "speed": access_uplink_speed,
                    "type": "fiber" if "10G" in access_uplink_speed else "copper",
                    "label": access_uplink_speed,
                })
            acc_idx += 1

    return {"nodes": nodes, "edges": edges}


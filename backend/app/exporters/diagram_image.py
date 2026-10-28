"""
diagram_image.py — Static network diagram generator using NetworkX + Matplotlib.
Spec Section 12.3.

Used when the frontend cannot provide a PNG screenshot (e.g., during PDF generation
without a browser). Returns a PNG as bytes.
"""
from __future__ import annotations

import io
import math
from typing import Any

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend — safe for server use
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import networkx as nx


# ── Color palette keyed by node layer/role ───────────────────────────────────
_ROLE_COLORS: dict[str, str] = {
    "internet":      "#94a3b8",
    "isp_router":    "#64748b",
    "firewall":      "#ef4444",
    "core":          "#6366f1",
    "distribution":  "#8b5cf6",
    "access":        "#3b82f6",
    "ap":            "#06b6d4",
    "wlc":           "#0ea5e9",
    "server_switch": "#f59e0b",
    "dmz":           "#f97316",
    "endpoint":      "#10b981",
}

_LAYER_ORDER: list[str] = [
    "internet", "edge", "core", "distribution", "access", "endpoint"
]


def _layer_rank(layer: str) -> int:
    try:
        return _LAYER_ORDER.index(layer)
    except ValueError:
        return len(_LAYER_ORDER)


def generate_diagram_png(graph: dict[str, Any], title: str = "Network Topology") -> bytes:
    """
    Render a hierarchical network topology diagram from the graph dict
    (produced by engine/graph_builder.py).

    Returns PNG image bytes.
    """
    nodes: list[dict] = graph.get("nodes", [])
    edges: list[dict] = graph.get("edges", [])

    if not nodes:
        return _empty_diagram(title)

    # ── Build NetworkX graph ──────────────────────────────────────────────────
    G = nx.DiGraph()
    for node in nodes:
        G.add_node(
            node["id"],
            label=node.get("label", node["id"]),
            layer=node.get("layer", "access"),
            node_type=node.get("type", "access"),
        )

    for edge in edges:
        G.add_edge(
            edge["source"],
            edge["target"],
            speed=edge.get("speed", ""),
            label=edge.get("label", ""),
        )

    # ── Compute hierarchical layout ───────────────────────────────────────────
    pos = _hierarchical_layout(G, nodes)

    # ── Figure setup ─────────────────────────────────────────────────────────
    fig_width = max(12, len(nodes) * 1.5)
    fig_height = max(8, len(_LAYER_ORDER) * 2)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.set_facecolor("#0f172a")
    fig.patch.set_facecolor("#0f172a")
    ax.axis("off")

    # ── Draw edges first (below nodes) ───────────────────────────────────────
    edge_labels = {}
    for u, v, data in G.edges(data=True):
        if u in pos and v in pos:
            speed = data.get("speed", "")
            edge_labels[(u, v)] = speed

    # Draw edges
    nx.draw_networkx_edges(
        G, pos, ax=ax,
        edge_color="#475569",
        arrows=False,
        width=1.5,
        style="solid",
        alpha=0.7,
    )

    # Edge speed labels
    if edge_labels:
        nx.draw_networkx_edge_labels(
            G, pos, edge_labels=edge_labels, ax=ax,
            font_size=6,
            font_color="#94a3b8",
            bbox=dict(boxstyle="round,pad=0.2", fc="#1e293b", ec="none", alpha=0.8),
        )

    # ── Draw nodes ───────────────────────────────────────────────────────────
    node_colors = []
    node_sizes = []
    for node_id in G.nodes():
        ntype = G.nodes[node_id].get("node_type", "access")
        color = _ROLE_COLORS.get(ntype, "#64748b")
        node_colors.append(color)
        # Scale size by importance
        if ntype in ("firewall", "core"):
            node_sizes.append(2200)
        elif ntype in ("distribution", "isp_router"):
            node_sizes.append(1600)
        else:
            node_sizes.append(1000)

    nx.draw_networkx_nodes(
        G, pos, ax=ax,
        node_color=node_colors,
        node_size=node_sizes,
        node_shape="s",
        alpha=0.9,
        linewidths=1.5,
        edgecolors="#ffffff",
    )

    # Node labels
    labels = {n: G.nodes[n].get("label", n) for n in G.nodes()}
    nx.draw_networkx_labels(
        G, pos, labels=labels, ax=ax,
        font_size=7,
        font_color="white",
        font_weight="bold",
    )

    # ── Legend ────────────────────────────────────────────────────────────────
    legend_items = []
    seen_types = {G.nodes[n].get("node_type", "access") for n in G.nodes()}
    for rtype, color in _ROLE_COLORS.items():
        if rtype in seen_types:
            legend_items.append(
                mpatches.Patch(color=color, label=rtype.replace("_", " ").title())
            )

    if legend_items:
        legend = ax.legend(
            handles=legend_items,
            loc="lower right",
            frameon=True,
            framealpha=0.85,
            facecolor="#1e293b",
            edgecolor="#334155",
            labelcolor="white",
            fontsize=7,
            title="Device Roles",
            title_fontsize=8,
        )
        legend.get_title().set_color("#94a3b8")

    # ── Layer labels on the left ──────────────────────────────────────────────
    layer_y_positions: dict[str, float] = {}
    for node_id, (x, y) in pos.items():
        layer = G.nodes[node_id].get("layer", "access")
        if layer not in layer_y_positions:
            layer_y_positions[layer] = y
        else:
            layer_y_positions[layer] = max(layer_y_positions[layer], y)

    x_min = min(x for x, y in pos.values()) if pos else 0
    for layer, y in layer_y_positions.items():
        ax.text(
            x_min - 0.15, y,
            layer.upper(),
            ha="right", va="center",
            fontsize=7,
            color="#64748b",
            fontweight="bold",
        )

    # ── Title ─────────────────────────────────────────────────────────────────
    ax.set_title(
        title,
        color="white",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )

    plt.tight_layout(pad=0.5)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _hierarchical_layout(G: nx.DiGraph, nodes: list[dict]) -> dict[str, tuple[float, float]]:
    """
    Assign (x, y) positions based on the 'layer' attribute.
    Nodes within the same layer are spread horizontally.
    """
    # Group nodes by layer
    layer_groups: dict[str, list[str]] = {}
    for node in nodes:
        nid = node["id"]
        layer = node.get("layer", "access")
        layer_groups.setdefault(layer, []).append(nid)

    # Sort layers top-to-bottom
    sorted_layers = sorted(layer_groups.keys(), key=_layer_rank)

    pos: dict[str, tuple[float, float]] = {}
    y = 1.0
    y_step = 1.0 / max(1, len(sorted_layers) - 1) if len(sorted_layers) > 1 else 1.0

    for idx, layer in enumerate(sorted_layers):
        layer_nodes = layer_groups[layer]
        n = len(layer_nodes)
        for j, nid in enumerate(sorted(layer_nodes)):
            x = (j + 1) / (n + 1)
            pos[nid] = (x, 1.0 - idx * y_step)

    return pos


def _empty_diagram(title: str) -> bytes:
    """Return a minimal placeholder PNG when no nodes are available."""
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.set_facecolor("#0f172a")
    fig.patch.set_facecolor("#0f172a")
    ax.text(0.5, 0.5, "No diagram data available", ha="center", va="center",
            color="white", fontsize=14)
    ax.axis("off")
    ax.set_title(title, color="white", fontsize=12)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.read()

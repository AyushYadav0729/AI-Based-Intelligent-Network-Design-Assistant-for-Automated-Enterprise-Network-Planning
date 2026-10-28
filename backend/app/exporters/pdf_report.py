"""
pdf_report.py — Professional PDF design report using ReportLab.
Spec Section 12.2.

Sections generated:
  1. Cover page
  2. Requirements summary
  3. Topology overview + diagram
  4. VLAN table
  5. IP plan with capacity (current vs future)
  6. Devices and cost
  7. Bandwidth and oversubscription
  8. Routing
  9. Security plan + ACL matrix
 10. Validation results
 11. Variant comparison
 12. Decision explanations
 13. Assumptions and limitations
"""
from __future__ import annotations

import base64
import io
from datetime import datetime, timezone
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import KeepInFrame

from app.exporters.diagram_image import generate_diagram_png
from app.schemas.design import DesignResult

# ── Brand colours ──────────────────────────────────────────────────────────
C_DARK   = colors.HexColor("#0f172a")
C_MID    = colors.HexColor("#1e293b")
C_BRAND  = colors.HexColor("#6366f1")
C_ACCENT = colors.HexColor("#8b5cf6")
C_GREEN  = colors.HexColor("#10b981")
C_RED    = colors.HexColor("#ef4444")
C_AMBER  = colors.HexColor("#f59e0b")
C_BLUE   = colors.HexColor("#3b82f6")
C_GRAY   = colors.HexColor("#94a3b8")
C_LIGHT  = colors.HexColor("#f1f5f9")
C_WHITE  = colors.white

PAGE_W, PAGE_H = A4


# ── Style helpers ──────────────────────────────────────────────────────────

def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("h1", fontSize=24, textColor=C_BRAND, spaceAfter=6, spaceBefore=0, fontName="Helvetica-Bold", leading=28),
        "h2": ParagraphStyle("h2", fontSize=14, textColor=C_DARK, spaceAfter=4, spaceBefore=10, fontName="Helvetica-Bold", leading=18),
        "h3": ParagraphStyle("h3", fontSize=11, textColor=C_BRAND, spaceAfter=3, spaceBefore=6, fontName="Helvetica-Bold", leading=14),
        "body": ParagraphStyle("body", fontSize=9, textColor=C_DARK, spaceAfter=3, leading=13, fontName="Helvetica"),
        "small": ParagraphStyle("small", fontSize=7.5, textColor=C_GRAY, spaceAfter=2, leading=10, fontName="Helvetica"),
        "center": ParagraphStyle("center", fontSize=9, alignment=TA_CENTER, textColor=C_DARK, fontName="Helvetica"),
        "caption": ParagraphStyle("caption", fontSize=8, textColor=C_GRAY, alignment=TA_CENTER, fontName="Helvetica-Oblique"),
        "cover_title": ParagraphStyle("cover_title", fontSize=32, textColor=C_WHITE, alignment=TA_CENTER, fontName="Helvetica-Bold", leading=38),
        "cover_sub": ParagraphStyle("cover_sub", fontSize=14, textColor=C_GRAY, alignment=TA_CENTER, fontName="Helvetica"),
        "badge_green": ParagraphStyle("badge_green", fontSize=8, textColor=C_GREEN, fontName="Helvetica-Bold"),
        "badge_red": ParagraphStyle("badge_red", fontSize=8, textColor=C_RED, fontName="Helvetica-Bold"),
        "badge_amber": ParagraphStyle("badge_amber", fontSize=8, textColor=C_AMBER, fontName="Helvetica-Bold"),
    }


def _hr(color: Any = C_BRAND, thickness: float = 0.75) -> HRFlowable:
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=4, spaceBefore=2)


def _section_header(title: str, st: dict) -> list:
    return [
        Spacer(1, 0.3 * cm),
        Paragraph(title, st["h2"]),
        _hr(),
    ]


def _table_style_base() -> list:
    return [
        ("BACKGROUND", (0, 0), (-1, 0), C_BRAND),
        ("TEXTCOLOR",  (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_LIGHT]),
        ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 1), (-1, -1), 7.5),
        ("GRID",       (0, 0), (-1, -1), 0.3, C_GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
    ]


# ── Page templates ─────────────────────────────────────────────────────────

class _HeaderFooterCanvas:
    """Mixin for doc-level header/footer drawing on every page."""


def _add_header_footer(canvas, doc):
    """Called by ReportLab on each page render."""
    canvas.saveState()
    # Header bar
    canvas.setFillColor(C_DARK)
    canvas.rect(0, PAGE_H - 1.8 * cm, PAGE_W, 1.8 * cm, fill=1, stroke=0)
    canvas.setFillColor(C_BRAND)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(1.5 * cm, PAGE_H - 1.1 * cm, "AI Network Design Assistant")
    canvas.setFillColor(C_GRAY)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(PAGE_W - 1.5 * cm, PAGE_H - 1.1 * cm, "Generated Design Report")

    # Footer bar
    canvas.setFillColor(C_LIGHT)
    canvas.rect(0, 0, PAGE_W, 1.2 * cm, fill=1, stroke=0)
    canvas.setFillColor(C_GRAY)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(1.5 * cm, 0.45 * cm, "SAMPLE — Review before deployment. Not a substitute for professional engineering.")
    canvas.drawRightString(PAGE_W - 1.5 * cm, 0.45 * cm, f"Page {doc.page}")
    canvas.restoreState()


# ── Section builders ───────────────────────────────────────────────────────

def _build_cover(org_name: str, variant: str, generated_at: str, st: dict) -> list:
    elements: list = []
    elements.append(Spacer(1, 5 * cm))
    elements.append(Paragraph("Enterprise Network Design Report", st["cover_title"]))
    elements.append(Spacer(1, 0.8 * cm))
    elements.append(Paragraph(f"Organisation: {org_name}", st["cover_sub"]))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph(f"Variant: {variant.replace('_', ' ').title()}", st["cover_sub"]))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph(f"Generated: {generated_at}", st["cover_sub"]))
    elements.append(Spacer(1, 3 * cm))
    elements.append(Paragraph(
        "⚠  SAMPLE ONLY — All configurations and cost figures are indicative.\n"
        "Review with a qualified network engineer before deployment.",
        st["caption"]
    ))
    elements.append(PageBreak())
    return elements


def _build_requirements(req_dict: dict, design: DesignResult, st: dict) -> list:
    elements = _section_header("1. Requirements Summary", st)
    depts = req_dict.get("departments", [])

    data = [
        ["Field", "Value"],
        ["Organisation", req_dict.get("org_name", "—")],
        ["Org Type", req_dict.get("org_type", "—").replace("_", " ").title()],
        ["Floors", str(req_dict.get("floors", "—"))],
        ["Total Departments", str(len(depts))],
        ["Total Current Users", str(sum(d.get("users", 0) for d in depts))],
        ["Internal Servers", str(req_dict.get("servers", {}).get("count", 0))],
        ["DMZ / Public-Facing Servers", str(req_dict.get("servers", {}).get("public_facing", 0))],
        ["Internet Bandwidth", f"{req_dict.get('internet_bandwidth_mbps', 0)} Mbps"],
        ["Redundancy", req_dict.get("redundancy", "none").replace("_", " ").title()],
        ["Wi-Fi Enabled", "Yes" if req_dict.get("wifi_enabled") else "No"],
        ["Guest Wi-Fi", "Yes" if req_dict.get("guest_wifi") else "No"],
        ["Remote Access VPN", "Yes" if req_dict.get("remote_access_vpn") else "No"],
        ["Growth Rate", f"{req_dict.get('growth_percent', 0):.0f}% over {req_dict.get('growth_years', 0)} years"],
        ["Budget", f"${req_dict.get('budget'):,.0f}" if req_dict.get("budget") else "No limit"],
        ["Base Network", req_dict.get("base_network", "10.0.0.0/16")],
    ]

    tbl = Table(data, colWidths=[7 * cm, 10 * cm])
    tbl.setStyle(TableStyle(_table_style_base()))
    elements.append(tbl)

    if depts:
        elements.append(Spacer(1, 0.4 * cm))
        elements.append(Paragraph("Department Details", st["h3"]))
        dept_data = [["Department", "Users", "Floor", "Type", "Security", "Guest", "Printers"]]
        for d in depts:
            dept_data.append([
                d.get("name", ""),
                str(d.get("users", 0)),
                str(d.get("floor", 0)),
                d.get("dept_type", "").replace("_", " ").title(),
                d.get("security_level", "").title(),
                "Yes" if d.get("needs_guest_access") else "No",
                str(d.get("wired_printers", 0)),
            ])
        dtbl = Table(dept_data, colWidths=[4.5 * cm, 2 * cm, 2 * cm, 3.5 * cm, 2.5 * cm, 2 * cm, 2 * cm])
        dtbl.setStyle(TableStyle(_table_style_base()))
        elements.append(dtbl)

    elements.append(PageBreak())
    return elements


def _build_topology(design: DesignResult, diagram_png: bytes | None, st: dict) -> list:
    elements = _section_header("2. Topology Overview", st)
    elements.append(Paragraph(
        f"Selected topology: <b>{design.topology.replace('_', ' ').title()}</b>",
        st["body"]
    ))
    elements.append(Spacer(1, 0.3 * cm))

    # Embed diagram
    png_bytes = diagram_png
    if not png_bytes:
        try:
            png_bytes = generate_diagram_png(
                design.graph,
                title=f"Network Topology — {design.topology.replace('_', ' ').title()}"
            )
        except Exception:
            png_bytes = None

    if png_bytes:
        img_buf = io.BytesIO(png_bytes)
        img = Image(img_buf, width=16 * cm, height=9 * cm)
        elements.append(img)
        elements.append(Paragraph("Figure 1: Auto-generated network topology diagram.", st["caption"]))
    else:
        elements.append(Paragraph("(Topology diagram not available.)", st["small"]))

    elements.append(PageBreak())
    return elements


def _build_vlan_table(design: DesignResult, st: dict) -> list:
    elements = _section_header("3. VLAN Plan", st)
    data = [["VLAN ID", "Name", "Purpose", "Department"]]
    for v in design.vlans:
        data.append([
            str(v.vlan_id),
            v.name,
            v.purpose,
            v.dept or "—",
        ])
    tbl = Table(data, colWidths=[2 * cm, 3.5 * cm, 7 * cm, 5 * cm])
    tbl.setStyle(TableStyle(_table_style_base()))
    elements.append(tbl)
    elements.append(Spacer(1, 0.3 * cm))
    return elements


def _build_ip_plan(design: DesignResult, st: dict) -> list:
    elements = _section_header("4. IP Address Plan (VLSM)", st)
    data = [["Subnet Name", "Network/Prefix", "Gateway", "Usable Hosts", "Required", "Util%", "HSRP Virtual"]]
    for s in design.subnets:
        util = f"{s.utilization_pct:.1f}%"
        hsrp = s.hsrp.get("virtual", "—") if s.hsrp else "—"
        data.append([
            s.name,
            f"{s.network}/{s.prefix}",
            s.gateway,
            str(s.usable_hosts),
            str(s.required_hosts),
            util,
            hsrp,
        ])

    tbl = Table(data, colWidths=[3.5 * cm, 3.5 * cm, 3 * cm, 2.2 * cm, 2.2 * cm, 1.8 * cm, 2.8 * cm])
    ts = _table_style_base()
    # Highlight high-utilization rows
    for i, s in enumerate(design.subnets, start=1):
        if s.utilization_pct > 85:
            ts.append(("BACKGROUND", (5, i), (5, i), C_AMBER))
    tbl.setStyle(TableStyle(ts))
    elements.append(tbl)

    if design.p2p_links:
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph("Point-to-Point Links (/30)", st["h3"]))
        p2p_data = [["P2P Link Name", "Network", "Host A", "Host B"]]
        for link in design.p2p_links:
            p2p_data.append([
                link.name,
                f"{link.network}/{link.prefix}",
                link.first_host,
                link.last_host,
            ])
        p2p_tbl = Table(p2p_data, colWidths=[5 * cm, 4 * cm, 4 * cm, 4 * cm])
        p2p_tbl.setStyle(TableStyle(_table_style_base()))
        elements.append(p2p_tbl)

    elements.append(PageBreak())
    return elements


def _build_devices_cost(design: DesignResult, st: dict) -> list:
    elements = _section_header("5. Devices & Cost Breakdown", st)

    # Device BOM table
    data = [["Role", "Model", "Qty", "Unit Price", "Total Price", "Location"]]
    for d in design.devices:
        data.append([
            d.role.replace("_", " ").title(),
            d.model,
            str(d.quantity),
            f"${d.unit_price:,.0f}",
            f"${d.total_price:,.0f}",
            d.location,
        ])

    tbl = Table(data, colWidths=[2.5 * cm, 6 * cm, 1.2 * cm, 2.5 * cm, 2.5 * cm, 2.8 * cm])
    tbl.setStyle(TableStyle(_table_style_base()))
    elements.append(tbl)

    # Cost breakdown summary
    cost = design.cost
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(Paragraph("Cost Summary", st["h3"]))

    summary_data = [
        ["Category", "Amount (USD)"],
        ["Hardware (Devices)", f"${cost.get('hardware_cost', 0):,.2f}"],
        ["Threat Licensing", f"${cost.get('license_cost', 0):,.2f}"],
        ["Structured Cabling", f"${cost.get('cabling_cost', 0):,.2f}"],
        ["Rack / UPS Allowance", f"${cost.get('rack_ups_cost', 0):,.2f}"],
        ["TOTAL", f"${cost.get('total_cost', 0):,.2f}"],
    ]
    stbl = Table(summary_data, colWidths=[10 * cm, 7 * cm])
    sts = _table_style_base()
    sts.append(("BACKGROUND", (0, -1), (-1, -1), C_BRAND))
    sts.append(("TEXTCOLOR", (0, -1), (-1, -1), C_WHITE))
    sts.append(("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"))
    stbl.setStyle(TableStyle(sts))
    elements.append(stbl)

    budget = cost.get("budget")
    total = cost.get("total_cost", 0)
    if budget:
        within = total <= budget
        status_text = f"✓ Within budget (${budget:,.0f})" if within else f"✗ Over budget by ${total - budget:,.0f}"
        badge_style = "badge_green" if within else "badge_red"
        elements.append(Spacer(1, 0.2 * cm))
        elements.append(Paragraph(status_text, st[badge_style]))

    elements.append(PageBreak())
    return elements


def _build_bandwidth(design: DesignResult, st: dict) -> list:
    elements = _section_header("6. Bandwidth & Oversubscription Analysis", st)
    bw = design.bandwidth

    elements.append(Paragraph(
        f"Total Access Demand: <b>{bw.get('total_access_demand_mbps', 0):.0f} Mbps</b> | "
        f"Server Traffic: <b>{bw.get('server_traffic_mbps', 0):.0f} Mbps</b> | "
        f"Core Demand: <b>{bw.get('core_demand_mbps', 0):.0f} Mbps</b>",
        st["body"]
    ))
    elements.append(Spacer(1, 0.3 * cm))

    links = bw.get("links", [])
    if links:
        link_data = [["Link Name", "Demand (Mbps)", "Speed", "Capacity (Mbps)", "Utilization%", "Oversub Ratio", "OK?"]]
        for lnk in links:
            ok_str = "✓" if lnk.get("oversubscription_ok") else "✗"
            link_data.append([
                lnk.get("link_name", ""),
                f"{lnk.get('demand_mbps', 0):.0f}",
                lnk.get("speed", ""),
                f"{lnk.get('capacity_mbps', 0):.0f}",
                f"{lnk.get('utilization_pct', 0):.1f}%",
                f"{lnk.get('oversubscription_ratio', 0):.1f}:1",
                ok_str,
            ])
        ltbl = Table(link_data, colWidths=[4 * cm, 2.5 * cm, 2 * cm, 2.8 * cm, 2.5 * cm, 2.5 * cm, 1.2 * cm])
        lts = _table_style_base()
        for i, lnk in enumerate(links, start=1):
            if not lnk.get("oversubscription_ok"):
                lts.append(("BACKGROUND", (6, i), (6, i), C_RED))
                lts.append(("TEXTCOLOR", (6, i), (6, i), C_WHITE))
        ltbl.setStyle(TableStyle(lts))
        elements.append(ltbl)

    elements.append(Spacer(1, 0.3 * cm))
    return elements


def _build_routing(design: DesignResult, st: dict) -> list:
    elements = _section_header("7. Routing Architecture", st)
    rout = design.routing

    data = [
        ["Parameter", "Value"],
        ["Protocol",              rout.get("protocol", "—")],
        ["Inter-VLAN Method",     rout.get("inter_vlan_method", "—").replace("_", " ").upper()],
        ["OSPF Area",             str(rout.get("ospf_area", "—"))],
        ["Default Route",         rout.get("default_route", "—")],
        ["Passive Interfaces",    ", ".join(rout.get("passive_interfaces", []))],
    ]
    tbl = Table(data, colWidths=[6 * cm, 11 * cm])
    tbl.setStyle(TableStyle(_table_style_base()))
    elements.append(tbl)

    rip_note = rout.get("rip_evaluation_note", "")
    if rip_note:
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph(f"<b>RIP Evaluation Note:</b> {rip_note}", st["small"]))

    elements.append(Spacer(1, 0.3 * cm))
    return elements


def _build_security(design: DesignResult, st: dict) -> list:
    elements = _section_header("8. Security Plan & ACL Matrix", st)
    sec = design.security

    # Summary flags
    flags = [
        ("Perimeter Firewall",    sec.get("perimeter_firewall")),
        ("DMZ Enabled",           sec.get("dmz_enabled")),
        ("Guest Isolated",        sec.get("guest_isolated")),
        ("NAT/PAT Enabled",       sec.get("nat_pat_enabled")),
        ("Remote Access VPN",     sec.get("remote_access_vpn")),
    ]
    flag_data = [["Security Feature", "Status"]]
    for name, val in flags:
        flag_data.append([name, "✓ Enabled" if val else "✗ Disabled"])
    ftbl = Table(flag_data, colWidths=[9 * cm, 8 * cm])
    fts = _table_style_base()
    for i, (_, val) in enumerate(flags, start=1):
        color = C_GREEN if val else C_RED
        fts.append(("TEXTCOLOR", (1, i), (1, i), color))
    ftbl.setStyle(TableStyle(fts))
    elements.append(ftbl)

    # Department policies
    dept_policies = sec.get("dept_policies", [])
    if dept_policies:
        elements.append(Spacer(1, 0.4 * cm))
        elements.append(Paragraph("Department Security Policies", st["h3"]))
        dp_data = [["Department", "Security Level", "802.1X", "DHCP Snooping", "DAI", "Direct Internet"]]
        for p in dept_policies:
            dp_data.append([
                p["dept_name"],
                p["security_level"].title(),
                "✓" if p.get("dot1x_enabled") else "—",
                "✓" if p.get("dhcp_snooping") else "—",
                "✓" if p.get("dai_enabled") else "—",
                "Yes" if p.get("direct_internet") else "No",
            ])
        dptbl = Table(dp_data, colWidths=[4 * cm, 3 * cm, 2 * cm, 3 * cm, 2 * cm, 3.5 * cm])
        dptbl.setStyle(TableStyle(_table_style_base()))
        elements.append(dptbl)

    # ACL Matrix heatmap (textual)
    acl_matrix: dict = sec.get("acl_matrix", {})
    if acl_matrix:
        elements.append(Spacer(1, 0.4 * cm))
        elements.append(Paragraph("Inter-VLAN ACL Matrix", st["h3"]))
        elements.append(Paragraph(
            "P = Permit  |  D = Deny  |  L = Limited (specific ports)",
            st["small"]
        ))
        vlan_names = list(acl_matrix.keys())
        header = ["SRC \\ DST"] + vlan_names
        matrix_data = [header]
        for src in vlan_names:
            row = [src]
            for dst in vlan_names:
                action = acl_matrix.get(src, {}).get(dst, "—")
                row.append("P" if action == "permit" else ("D" if action == "deny" else "L"))
            matrix_data.append(row)
        n = len(vlan_names)
        col_w = min(2.5 * cm, 17 * cm / (n + 1))
        mtbl = Table(matrix_data, colWidths=[2.5 * cm] + [col_w] * n)
        mts = [
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.3, C_GRAY),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("BACKGROUND", (0, 0), (-1, 0), C_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
            ("BACKGROUND", (0, 1), (0, -1), C_DARK),
            ("TEXTCOLOR", (0, 1), (0, -1), C_WHITE),
        ]
        # Colour cells by action
        for r_i, src in enumerate(vlan_names, start=1):
            for c_i, dst in enumerate(vlan_names, start=1):
                action = acl_matrix.get(src, {}).get(dst, "—")
                if action == "permit":
                    mts.append(("BACKGROUND", (c_i, r_i), (c_i, r_i), colors.HexColor("#bbf7d0")))
                elif action == "deny":
                    mts.append(("BACKGROUND", (c_i, r_i), (c_i, r_i), colors.HexColor("#fecaca")))
                else:
                    mts.append(("BACKGROUND", (c_i, r_i), (c_i, r_i), colors.HexColor("#fef3c7")))
        mtbl.setStyle(TableStyle(mts))
        elements.append(mtbl)

    elements.append(PageBreak())
    return elements


def _build_validation(design: DesignResult, st: dict) -> list:
    elements = _section_header("9. Validation Results", st)
    issues = design.validation

    errors   = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    infos    = [i for i in issues if i.severity == "info"]

    elements.append(Paragraph(
        f"<b>Errors: {len(errors)}</b>  |  Warnings: {len(warnings)}  |  Info: {len(infos)}",
        st["body"]
    ))

    if not issues:
        elements.append(Spacer(1, 0.2 * cm))
        elements.append(Paragraph("✓ All 21 validation rules passed — no issues found.", st["badge_green"]))
    else:
        issue_data = [["Severity", "Code", "Message"]]
        for issue in sorted(issues, key=lambda x: {"error": 0, "warning": 1, "info": 2}[x.severity]):
            issue_data.append([
                issue.severity.upper(),
                issue.code,
                issue.message,
            ])
        itbl = Table(issue_data, colWidths=[2.5 * cm, 4.5 * cm, 10.5 * cm])
        its = _table_style_base()
        for i, issue in enumerate(sorted(issues, key=lambda x: {"error": 0, "warning": 1, "info": 2}[x.severity]), start=1):
            if issue.severity == "error":
                its.append(("TEXTCOLOR", (0, i), (0, i), C_RED))
            elif issue.severity == "warning":
                its.append(("TEXTCOLOR", (0, i), (0, i), C_AMBER))
            else:
                its.append(("TEXTCOLOR", (0, i), (0, i), C_BLUE))
        itbl.setStyle(TableStyle(its))
        elements.append(itbl)

    elements.append(Spacer(1, 0.3 * cm))
    return elements


def _build_comparison(comparison: list[dict], summary: str, st: dict) -> list:
    elements = _section_header("10. Variant Comparison", st)
    if summary:
        elements.append(Paragraph(summary, st["body"]))
        elements.append(Spacer(1, 0.3 * cm))

    if comparison:
        # Pivot: metric, budget, balanced, high_performance
        header = ["Metric", "Budget", "Balanced", "High-Performance"]
        comp_data = [header]
        for row in comparison:
            metric = row.get("metric", "").replace("_", " ").title()
            comp_data.append([
                metric,
                str(row.get("budget", "—")),
                str(row.get("balanced", "—")),
                str(row.get("high_performance", "—")),
            ])
        ctbl = Table(comp_data, colWidths=[6 * cm, 3.7 * cm, 3.7 * cm, 4.1 * cm])
        cts = _table_style_base()
        # Highlight balanced column
        for i in range(1, len(comp_data)):
            cts.append(("BACKGROUND", (2, i), (2, i), colors.HexColor("#e0e7ff")))
        ctbl.setStyle(TableStyle(cts))
        elements.append(ctbl)

    elements.append(Spacer(1, 0.3 * cm))
    return elements


def _build_decisions(design: DesignResult, st: dict) -> list:
    elements = _section_header("11. Design Decision Log", st)
    for dec in design.decisions:
        elements.append(Paragraph(
            f"<b>[{dec.stage.upper()}]</b> {dec.choice}",
            st["h3"]
        ))
        if dec.explanation:
            elements.append(Paragraph(dec.explanation, st["body"]))
        else:
            elements.append(Paragraph(
                f"Reason: {dec.reason_code}  |  Params: {dec.params}",
                st["small"]
            ))
        elements.append(Spacer(1, 0.15 * cm))

    elements.append(Spacer(1, 0.3 * cm))
    return elements


def _build_assumptions(st: dict) -> list:
    elements = _section_header("12. Assumptions & Limitations", st)
    items = [
        "Single-site campus LAN only; no WAN, BGP, or multi-site design.",
        "IPv4 only; IPv6 / dual-stack planned as a future extension.",
        "Device catalog uses representative pricing — not live vendor quotes.",
        "Bandwidth model uses planning estimates, not measured traffic data.",
        "No VoIP, CCTV, or IoT QoS modelling in this version.",
        "All CLI configs are samples requiring review before production deployment.",
        "OSPF Area 0 is used for all enterprise designs; multi-area OSPF is future work.",
        "PoE budgets are not explicitly calculated; verify against switch PoE power ratings.",
        "Wi-Fi capacity model: 25 concurrent clients per AP (configurable).",
        "Growth projection uses compound percentage; actual growth may vary.",
        "LLM explanations (Gemini) are advisory and do not change the deterministic design.",
    ]
    for item in items:
        elements.append(Paragraph(f"• {item}", st["body"]))
    elements.append(Spacer(1, 0.3 * cm))
    return elements


# ── Public API ─────────────────────────────────────────────────────────────

def generate_pdf_report(
    design: DesignResult,
    requirements: dict,
    comparison: list[dict] | None = None,
    comparison_summary: str = "",
    diagram_png_b64: str | None = None,
) -> bytes:
    """
    Generate a full PDF design report for the given DesignResult.

    Args:
        design:              The DesignResult for the selected variant.
        requirements:        The RequirementsInput as a plain dict.
        comparison:          Optional comparison table rows.
        comparison_summary:  Optional summary paragraph from LLM/template.
        diagram_png_b64:     Optional Base64-encoded PNG from the browser
                             (React Flow canvas export). If None, falls back
                             to the server-side NetworkX+Matplotlib renderer.

    Returns:
        PDF as bytes.
    """
    st = _styles()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    org_name = requirements.get("org_name", "Unknown Organisation")
    variant = design.variant

    # Decode diagram if provided
    diagram_png: bytes | None = None
    if diagram_png_b64:
        try:
            diagram_png = base64.b64decode(diagram_png_b64)
        except Exception:
            diagram_png = None

    # ── Document setup ────────────────────────────────────────────────────────
    buf = io.BytesIO()
    doc = BaseDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=1.8 * cm,
    )

    # Single page template with header/footer
    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="normal",
    )
    template = PageTemplate(id="main", frames=[frame], onPage=_add_header_footer)
    doc.addPageTemplates([template])

    # ── Build story ───────────────────────────────────────────────────────────
    story: list = []
    story += _build_cover(org_name, variant, now, st)
    story += _build_requirements(requirements, design, st)
    story += _build_topology(design, diagram_png, st)
    story += _build_vlan_table(design, st)
    story += _build_ip_plan(design, st)
    story += _build_devices_cost(design, st)
    story += _build_bandwidth(design, st)
    story += _build_routing(design, st)
    story += _build_security(design, st)
    story += _build_validation(design, st)
    if comparison is not None:
        story += _build_comparison(comparison, comparison_summary, st)
    story += _build_decisions(design, st)
    story += _build_assumptions(st)

    doc.build(story)
    buf.seek(0)
    return buf.read()

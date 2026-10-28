"""
test_llm_fallback.py — Tests for LLM integration, fallback templates, and numeric sanity guard.
Spec Section 15:
- mock Gemini failure/timeout/invalid JSON -> verify fallback templates and form-only behavior
- verify numeric sanity guard rejects explanations containing unknown numbers
"""
import pytest
from unittest.mock import patch

from app.schemas.requirements import RequirementsInput, Department, ServerSpec
from app.schemas.design import Decision
from app.llm.fallback_templates import render_template_explanation, TEMPLATES
from app.llm.explainer import verify_numeric_sanity, explain_decisions
from app.llm.parser import parse_free_text_requirements
from app.engine.pipeline import run_pipeline


def test_fallback_templates_render_for_all_registered_codes():
    """All registered reason_code templates render without Jinja2 syntax errors."""
    sample_params = {
        "total_planned_users": 150,
        "floors": 2,
        "access_switch_count": 4,
        "max_star_users": 100,
        "max_star_floors": 2,
        "max_collapsed_users": 800,
        "max_collapsed_floors": 4,
        "core_count": 2,
        "firewall_count": 2,
        "uplinks_per_access": 2,
        "hsrp_enabled": True,
        "etherchannel_enabled": True,
        "target_utilization": 0.7,
        "total_access_demand_mbps": 450.0,
        "server_traffic_mbps": 100.0,
        "core_demand_mbps": 550.0,
        "original_pool": "10.0.0.0/16",
        "expanded_pool": "10.0.0.0/12",
        "tier": "mid",
        "port_headroom": 0.20,
        "total_access_switches": 4,
        "total_aps": 6,
        "wlc_required": False,
        "protocol": "OSPF",
        "subnet_count": 6,
        "l3_device_count": 2,
        "total_cost": 25000.0,
        "devices_cost": 15000.0,
        "licenses_cost": 1000.0,
        "cabling_cost": 5000.0,
        "rack_ups_cost": 4000.0,
        "within_budget": True,
    }

    for code in TEMPLATES:
        rendered = render_template_explanation(code, sample_params)
        assert isinstance(rendered, str)
        assert len(rendered) > 20
        assert "{{" not in rendered, f"Unrendered Jinja tag in template {code}"


def test_numeric_sanity_guard_accepts_valid_numbers():
    params = {"total_planned_users": 350, "floors": 3, "utilization": 70}
    # Valid: 350, 3, 70 exist in params, and 2 is a safe common number
    valid_explanation = (
        "Selected collapsed core for 350 planned users across 3 floors with 2 core links at 70% utilization."
    )
    assert verify_numeric_sanity(valid_explanation, params) is True


def test_numeric_sanity_guard_rejects_hallucinated_numbers():
    params = {"total_planned_users": 350, "floors": 3}
    # Hallucinated: 9999 and 876 do not exist in params
    hallucinated_explanation = (
        "Selected collapsed core costing $9999 supporting 876 devices."
    )
    assert verify_numeric_sanity(hallucinated_explanation, params) is False


def test_explain_decisions_graceful_template_fallback():
    """When no LLM key or LLM fails, explain_decisions enriches every decision with templates."""
    decisions = [
        Decision(
            stage="topology",
            choice="collapsed_core",
            reason_code="TOPO_COLLAPSED_CORE_MID_NETWORK",
            params={
                "total_planned_users": 200,
                "floors": 2,
                "access_switch_count": 5,
                "max_collapsed_users": 800,
                "max_collapsed_floors": 4,
            },
        ),
        Decision(
            stage="routing",
            choice="OSPF",
            reason_code="ROUTING_OSPF_ENTERPRISE_CONVERGENCE",
            params={"subnet_count": 6, "l3_device_count": 2},
        ),
    ]

    with patch("app.llm.explainer.is_llm_available", return_value=False):
        enriched, source = explain_decisions(decisions)

    assert source == "template"
    assert len(enriched) == 2
    for d in enriched:
        assert d.explanation is not None
        assert len(d.explanation) > 15
        assert "collapsed core" in enriched[0].explanation.lower()


def test_parse_free_text_graceful_fallback_without_key():
    """When Gemini is not available, parser returns source='none' with message without crashing."""
    with patch("app.llm.parser.is_llm_available", return_value=False):
        result = parse_free_text_requirements("School with 3 floors and 200 students")

    assert result.source == "none"
    assert result.requirements is None
    assert "not configured" in result.message.lower() or "unavailable" in result.message.lower()


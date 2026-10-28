"""
variants.py — Multi-variant generator (Budget, Balanced, High-performance) and comparison engine.
Spec Section 6.10.
"""
from typing import Any
from app.schemas.requirements import RequirementsInput
from app.schemas.design import DesignResult, DesignGenerateResponse
from app.engine.pipeline import run_pipeline
from app.llm.explainer import explain_decisions


def generate_comparison_table(
    budget_res: DesignResult,
    balanced_res: DesignResult,
    high_res: DesignResult,
    req: RequirementsInput,
) -> list[dict[str, Any]]:
    """
    Builds structured side-by-side comparison table rows across the 3 variants.
    """
    def _dev_count(res: DesignResult) -> int:
        return sum(d.quantity for d in res.devices)

    def _worst_oversub(res: DesignResult) -> str:
        links = res.bandwidth.get("links", [])
        if not links:
            return "N/A"
        max_ratio = max((l.get("oversubscription_ratio", 1.0) for l in links), default=1.0)
        return f"{max_ratio:.1f}:1"

    def _core_speed(res: DesignResult) -> str:
        links = res.bandwidth.get("links", [])
        core_link = next((l for l in links if "Core" in l.get("link_name", "")), None)
        return core_link.get("speed", "10G") if core_link else "10G"

    def _access_speed(res: DesignResult) -> str:
        links = res.bandwidth.get("links", [])
        acc_link = next((l for l in links if "Access" in l.get("link_name", "")), None)
        return acc_link.get("speed", "1G") if acc_link else "1G"

    def _budget_status(res: DesignResult) -> str:
        if req.budget is None:
            return "No limit set"
        cost = res.cost.get("total_cost", 0.0)
        if cost <= req.budget:
            return f"Within budget (${req.budget - cost:,.0f} under)"
        return f"Over budget (${cost - req.budget:,.0f} over)"

    def _issue_count(res: DesignResult, sev: str) -> int:
        return sum(1 for i in res.validation if i.severity == sev)

    metrics = [
        {
            "metric": "total_cost",
            "label": "Total Estimated Cost",
            "budget": f"${budget_res.cost.get('total_cost', 0):,.2f}",
            "balanced": f"${balanced_res.cost.get('total_cost', 0):,.2f}",
            "high_performance": f"${high_res.cost.get('total_cost', 0):,.2f}",
        },
        {
            "metric": "budget_status",
            "label": "Budget Compliance",
            "budget": _budget_status(budget_res),
            "balanced": _budget_status(balanced_res),
            "high_performance": _budget_status(high_res),
        },
        {
            "metric": "topology",
            "label": "Network Topology",
            "budget": budget_res.topology.replace("_", " ").title(),
            "balanced": balanced_res.topology.replace("_", " ").title(),
            "high_performance": high_res.topology.replace("_", " ").title(),
        },
        {
            "metric": "device_count",
            "label": "Total Device Units",
            "budget": _dev_count(budget_res),
            "balanced": _dev_count(balanced_res),
            "high_performance": _dev_count(high_res),
        },
        {
            "metric": "access_uplink_speed",
            "label": "Access Uplink Speed",
            "budget": _access_speed(budget_res),
            "balanced": _access_speed(balanced_res),
            "high_performance": _access_speed(high_res),
        },
        {
            "metric": "core_speed",
            "label": "Core / Interconnect Speed",
            "budget": _core_speed(budget_res),
            "balanced": _core_speed(balanced_res),
            "high_performance": _core_speed(high_res),
        },
        {
            "metric": "redundancy",
            "label": "Redundancy Architecture",
            "budget": budget_res.routing.get("redundancy", req.redundancy).replace("_", " ").title(),
            "balanced": balanced_res.routing.get("redundancy", req.redundancy).replace("_", " ").title(),
            "high_performance": f"{high_res.routing.get('redundancy', req.redundancy).replace('_', ' ').title()} (Tier Upgraded)",
        },
        {
            "metric": "worst_oversubscription",
            "label": "Worst Oversubscription",
            "budget": _worst_oversub(budget_res),
            "balanced": _worst_oversub(balanced_res),
            "high_performance": _worst_oversub(high_res),
        },
        {
            "metric": "validation_issues",
            "label": "Validation Issues (Errors / Warnings)",
            "budget": f"{_issue_count(budget_res, 'error')} errors, {_issue_count(budget_res, 'warning')} warnings",
            "balanced": f"{_issue_count(balanced_res, 'error')} errors, {_issue_count(balanced_res, 'warning')} warnings",
            "high_performance": f"{_issue_count(high_res, 'error')} errors, {_issue_count(high_res, 'warning')} warnings",
        },
    ]

    return metrics


def generate_comparison_summary(
    budget_res: DesignResult,
    balanced_res: DesignResult,
    high_res: DesignResult,
    req: RequirementsInput,
) -> str:
    """
    Template-based deterministic executive comparison summary.
    Used as primary output and fallback for the LLM.
    """
    b_cost = budget_res.cost.get("total_cost", 0.0)
    bal_cost = balanced_res.cost.get("total_cost", 0.0)
    h_cost = high_res.cost.get("total_cost", 0.0)

    summary = (
        f"The Balanced design represents the recommended baseline at ${bal_cost:,.2f}, balancing 20% port headroom "
        f"and mid-tier throughput suitable for anticipated {req.growth_percent}% growth over {req.growth_years} years. "
        f"The Budget design lowers capital expenditure to ${b_cost:,.2f} using 10% port headroom and value-tier access "
        f"switches. The High-Performance tier at ${h_cost:,.2f} delivers maximum resiliency with 30% headroom, 10G/40G links, "
        f"and elevated redundancy."
    )
    return summary


def generate_all_variants(req: RequirementsInput) -> DesignGenerateResponse:
    """
    Runs the pipeline across all 3 variants (budget, balanced, high_performance),
    enriches decisions with explanations (LLM or template fallback),
    and produces the comparative analysis response.
    """
    budget_design = run_pipeline(req, variant="budget")
    balanced_design = run_pipeline(req, variant="balanced")
    high_design = run_pipeline(req, variant="high_performance")

    # Enrich decisions with explanations
    b_decs, _ = explain_decisions(budget_design.decisions)
    bal_decs, bal_src = explain_decisions(balanced_design.decisions)
    h_decs, _ = explain_decisions(high_design.decisions)

    budget_design = budget_design.model_copy(update={"decisions": b_decs})
    balanced_design = balanced_design.model_copy(update={"decisions": bal_decs})
    high_design = high_design.model_copy(update={"decisions": h_decs})

    comparison = generate_comparison_table(
        budget_res=budget_design,
        balanced_res=balanced_design,
        high_res=high_design,
        req=req,
    )

    summary = generate_comparison_summary(
        budget_res=budget_design,
        balanced_res=balanced_design,
        high_res=high_design,
        req=req,
    )

    return DesignGenerateResponse(
        variants={
            "budget": budget_design,
            "balanced": balanced_design,
            "high_performance": high_design,
        },
        comparison=comparison,
        comparison_summary=summary,
        explanation_source=bal_src,
    )


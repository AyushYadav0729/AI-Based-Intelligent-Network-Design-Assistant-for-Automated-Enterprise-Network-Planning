"""
test_variants.py — Tests for 3-variant generation and comparison table.
Spec Section 16 (Phase 5 acceptance criteria):
- scenarios return 3 variants with comparison.
"""
from pathlib import Path
import json
import pytest

from app.schemas.requirements import RequirementsInput
from app.schemas.design import DesignGenerateResponse
from app.engine.variants import generate_all_variants

SCENARIOS_DIR = Path(__file__).parent / "scenarios"


@pytest.mark.parametrize(
    "scenario_name",
    [
        "small_office.json",
        "school.json",
        "hospital.json",
        "it_company.json",
    ],
)
def test_generate_all_variants_for_scenarios(scenario_name: str):
    with open(SCENARIOS_DIR / scenario_name, "r", encoding="utf-8") as f:
        data = json.load(f)
    req = RequirementsInput.model_validate(data)

    res = generate_all_variants(req)
    assert isinstance(res, DesignGenerateResponse)
    assert "budget" in res.variants
    assert "balanced" in res.variants
    assert "high_performance" in res.variants

    # Verify cost progression: budget <= balanced <= high_performance
    b_cost = res.variants["budget"].cost["total_cost"]
    bal_cost = res.variants["balanced"].cost["total_cost"]
    h_cost = res.variants["high_performance"].cost["total_cost"]
    assert b_cost <= bal_cost <= h_cost

    # Verify comparison table
    assert len(res.comparison) >= 8
    metrics = {row["metric"] for row in res.comparison}
    assert "total_cost" in metrics
    assert "topology" in metrics
    assert "device_count" in metrics
    assert "worst_oversubscription" in metrics

    # Verify comparison summary exists
    assert len(res.comparison_summary) > 20


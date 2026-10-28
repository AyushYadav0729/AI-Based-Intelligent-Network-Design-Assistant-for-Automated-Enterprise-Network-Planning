"""
test_api_and_persistence.py — Integration tests for API endpoints and SQLite persistence.
Acceptance criteria for Phase 6:
- generate -> save -> list -> load -> delete works.
- validate endpoint works.
- catalog endpoint works.
- project comparison works.
"""
from pathlib import Path
import json
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.requirements import RequirementsInput

SCENARIOS_DIR = Path(__file__).parent / "scenarios"
client = TestClient(app)


@pytest.fixture
def sample_req() -> dict:
    with open(SCENARIOS_DIR / "small_office.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def school_req() -> dict:
    with open(SCENARIOS_DIR / "school.json", "r", encoding="utf-8") as f:
        return json.load(f)


def test_api_catalog():
    """GET /api/catalog returns the hardware device catalog."""
    res = client.get("/api/catalog")
    assert res.status_code == 200
    data = res.json()
    assert data["currency"] == "USD"
    assert len(data["devices"]) >= 20


def test_api_design_generate(sample_req: dict):
    """POST /api/design/generate returns 3 variants + comparison."""
    res = client.post("/api/design/generate", json=sample_req)
    assert res.status_code == 200
    data = res.json()
    assert "variants" in data
    assert "budget" in data["variants"]
    assert "balanced" in data["variants"]
    assert "high_performance" in data["variants"]
    assert len(data["comparison"]) >= 8
    assert "comparison_summary" in data


def test_api_design_validate(sample_req: dict):
    """POST /api/design/validate re-runs validation rules."""
    gen_res = client.post("/api/design/generate", json=sample_req)
    assert gen_res.status_code == 200
    design = gen_res.json()["variants"]["balanced"]

    # Valid design
    val_res = client.post(
        "/api/design/validate",
        json={"design": design, "requirements": sample_req},
    )
    assert val_res.status_code == 200
    data = val_res.json()
    assert data["error_count"] == 0

    # Invalid design (overlap)
    bad_design = dict(design)
    bad_subnets = list(bad_design["subnets"])
    bad_subnets[1]["network"] = bad_subnets[0]["network"]
    bad_subnets[1]["prefix"] = bad_subnets[0]["prefix"]
    bad_design["subnets"] = bad_subnets

    bad_val_res = client.post(
        "/api/design/validate",
        json={"design": bad_design, "requirements": sample_req},
    )
    assert bad_val_res.status_code == 200
    bad_data = bad_val_res.json()
    assert bad_data["error_count"] > 0
    assert any(i["code"] == "ADDR_OVERLAP" for i in bad_data["issues"])


def test_project_lifecycle_generate_save_list_load_compare_delete(sample_req: dict, school_req: dict):
    """Full lifecycle: generate -> save -> list -> load -> compare -> delete."""
    # 1. Generate design for Small Office
    gen_res1 = client.post("/api/design/generate", json=sample_req)
    assert gen_res1.status_code == 200
    design_data1 = gen_res1.json()

    # 2. Save Small Office project
    save_res1 = client.post(
        "/api/projects",
        json={
            "name": "Small Office Project",
            "requirements": sample_req,
            "results": design_data1,
            "explanation_source": "template",
        },
    )
    assert save_res1.status_code == 201
    proj1 = save_res1.json()
    proj1_id = proj1["id"]
    assert proj1["name"] == "Small Office Project"

    # 3. Generate and Save School project
    gen_res2 = client.post("/api/design/generate", json=school_req)
    assert gen_res2.status_code == 200
    design_data2 = gen_res2.json()

    save_res2 = client.post(
        "/api/projects",
        json={
            "name": "Pine Valley Academy",
            "requirements": school_req,
            "results": design_data2,
            "explanation_source": "template",
        },
    )
    assert save_res2.status_code == 201
    proj2 = save_res2.json()
    proj2_id = proj2["id"]

    # 4. List projects
    list_res = client.get("/api/projects")
    assert list_res.status_code == 200
    projects_list = list_res.json()
    saved_ids = [p["id"] for p in projects_list]
    assert proj1_id in saved_ids
    assert proj2_id in saved_ids

    # 5. Load project 1
    load_res = client.get(f"/api/projects/{proj1_id}")
    assert load_res.status_code == 200
    loaded = load_res.json()
    assert loaded["id"] == proj1_id
    assert loaded["requirements"]["org_name"] == sample_req["org_name"]
    assert "variants" in loaded["results"]

    # 6. Compare projects
    comp_res = client.get(f"/api/projects/compare?ids={proj1_id},{proj2_id}")
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert len(comp_data["projects"]) == 2
    assert len(comp_data["comparison_metrics"]) >= 5

    # 7. Delete project 1 and 2
    del_res1 = client.delete(f"/api/projects/{proj1_id}")
    assert del_res1.status_code == 204

    del_res2 = client.delete(f"/api/projects/{proj2_id}")
    assert del_res2.status_code == 204

    # 8. Verify project 1 is gone (404)
    gone_res = client.get(f"/api/projects/{proj1_id}")
    assert gone_res.status_code == 404


"""
test_exporters.py — Unit tests for Phase 9 exporters.
Spec Section 15: test_exporters.py
  - CLI configs render without template errors
  - PDF generates a non-empty file
"""
import io
import json
import zipfile
from pathlib import Path

import pytest

# ── Shared fixture: build a minimal DesignResult from the hospital scenario ──

SCENARIO_DIR = Path(__file__).parent / "scenarios"


def _load_hospital_result():
    """Run the pipeline on the hospital scenario to get a real DesignResult."""
    from app.schemas.requirements import RequirementsInput
    from app.engine.pipeline import run_pipeline

    hospital_path = SCENARIO_DIR / "hospital.json"
    req = RequirementsInput.model_validate_json(hospital_path.read_text(encoding="utf-8"))
    return run_pipeline(req, variant="balanced"), req


@pytest.fixture(scope="module")
def hospital_result():
    result, req = _load_hospital_result()
    return result, req


# ── CLI Config Tests ─────────────────────────────────────────────────────────

class TestCliConfigs:
    """Test that CLI config templates render without errors."""

    def test_cli_configs_generated(self, hospital_result):
        """generate_cli_configs returns a non-empty dict."""
        from app.exporters.cli_config import generate_cli_configs
        design, _ = hospital_result
        configs = generate_cli_configs(design)
        assert isinstance(configs, dict)
        assert len(configs) > 0, "Should generate at least one config file"

    def test_readme_included(self, hospital_result):
        """README.txt is always included in the output."""
        from app.exporters.cli_config import generate_cli_configs
        design, _ = hospital_result
        configs = generate_cli_configs(design)
        assert "README.txt" in configs
        assert "SAMPLE" in configs["README.txt"]

    def test_core_switch_config_present(self, hospital_result):
        """At least one core switch config is generated."""
        from app.exporters.cli_config import generate_cli_configs
        design, _ = hospital_result
        configs = generate_cli_configs(design)
        core_files = [k for k in configs if k.startswith("CORE-SW")]
        assert len(core_files) >= 1, "At least one CORE-SW config expected"

    def test_access_switch_config_present(self, hospital_result):
        """At least one access switch config is generated."""
        from app.exporters.cli_config import generate_cli_configs
        design, _ = hospital_result
        configs = generate_cli_configs(design)
        acc_files = [k for k in configs if k.startswith("ACC-SW")]
        assert len(acc_files) >= 1, "At least one ACC-SW config expected"

    def test_firewall_config_present(self, hospital_result):
        """At least one firewall config is generated."""
        from app.exporters.cli_config import generate_cli_configs
        design, _ = hospital_result
        configs = generate_cli_configs(design)
        fw_files = [k for k in configs if k.startswith("FW-EDGE")]
        assert len(fw_files) >= 1, "At least one FW-EDGE config expected"

    def test_core_config_contains_vlan_defs(self, hospital_result):
        """Core switch config must contain VLAN definition commands."""
        from app.exporters.cli_config import generate_cli_configs
        design, _ = hospital_result
        configs = generate_cli_configs(design)
        core_conf = next((v for k, v in configs.items() if k.startswith("CORE-SW")), "")
        assert "vlan " in core_conf.lower(), "Expected 'vlan' definition in core config"

    def test_core_config_contains_ssh(self, hospital_result):
        """Core switch config must contain SSH hardening."""
        from app.exporters.cli_config import generate_cli_configs
        design, _ = hospital_result
        configs = generate_cli_configs(design)
        core_conf = next((v for k, v in configs.items() if k.startswith("CORE-SW")), "")
        assert "ip ssh version 2" in core_conf

    def test_access_config_contains_port_security(self, hospital_result):
        """Access switch config must mention port-security."""
        from app.exporters.cli_config import generate_cli_configs
        design, _ = hospital_result
        configs = generate_cli_configs(design)
        acc_conf = next((v for k, v in configs.items() if k.startswith("ACC-SW")), "")
        assert "port-security" in acc_conf.lower()

    def test_access_config_contains_dhcp_snooping(self, hospital_result):
        """Access switch config must include DHCP snooping."""
        from app.exporters.cli_config import generate_cli_configs
        design, _ = hospital_result
        configs = generate_cli_configs(design)
        acc_conf = next((v for k, v in configs.items() if k.startswith("ACC-SW")), "")
        assert "dhcp snooping" in acc_conf.lower()

    def test_firewall_config_nat(self, hospital_result):
        """Firewall config must include NAT configuration."""
        from app.exporters.cli_config import generate_cli_configs
        design, _ = hospital_result
        configs = generate_cli_configs(design)
        fw_conf = next((v for k, v in configs.items() if k.startswith("FW-EDGE")), "")
        assert "nat" in fw_conf.lower()

    def test_config_contains_sample_warning(self, hospital_result):
        """Every device config should carry the 'Generated sample' warning."""
        from app.exporters.cli_config import generate_cli_configs
        design, _ = hospital_result
        configs = generate_cli_configs(design)
        for fname, content in configs.items():
            if fname.endswith(".txt") and fname != "README.txt":
                assert "Generated sample" in content, f"Missing sample warning in {fname}"

    def test_configs_zip_roundtrip(self, hospital_result):
        """Configs can be assembled into a valid ZIP archive."""
        from app.exporters.cli_config import generate_cli_configs
        design, _ = hospital_result
        configs = generate_cli_configs(design)

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for fname, content in configs.items():
                zf.writestr(fname, content.encode("utf-8"))
        buf.seek(0)

        # Read back and verify
        with zipfile.ZipFile(buf) as zf:
            names = zf.namelist()
        assert "README.txt" in names
        assert any(n.startswith("CORE-SW") for n in names)

    def test_all_four_scenarios(self):
        """All four demo scenarios generate CLI configs without errors."""
        from app.schemas.requirements import RequirementsInput
        from app.engine.pipeline import run_pipeline
        from app.exporters.cli_config import generate_cli_configs

        for scenario_name in ["small_office", "school", "hospital", "it_company"]:
            scenario_path = SCENARIO_DIR / f"{scenario_name}.json"
            req = RequirementsInput.model_validate_json(scenario_path.read_text(encoding="utf-8"))
            design = run_pipeline(req, variant="balanced")
            configs = generate_cli_configs(design)
            assert len(configs) > 1, f"Expected multiple files for {scenario_name}"


# ── PDF Report Tests ─────────────────────────────────────────────────────────

class TestPdfReport:
    """Test that the PDF report generates correctly."""

    def test_pdf_generates_non_empty(self, hospital_result):
        """PDF bytes are non-empty and start with the PDF header."""
        from app.exporters.pdf_report import generate_pdf_report
        design, req = hospital_result
        req_dict = req.model_dump()

        pdf_bytes = generate_pdf_report(design=design, requirements=req_dict)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 5000, "PDF should be at least 5 KB"
        assert pdf_bytes[:4] == b"%PDF", "Output should start with PDF header"

    def test_pdf_with_comparison(self, hospital_result):
        """PDF with comparison data generates without errors."""
        from app.exporters.pdf_report import generate_pdf_report
        design, req = hospital_result
        req_dict = req.model_dump()

        comparison = [
            {"metric": "total_cost", "budget": 10000, "balanced": 15000, "high_performance": 22000},
            {"metric": "topology", "budget": "three_tier", "balanced": "three_tier", "high_performance": "three_tier"},
        ]
        pdf_bytes = generate_pdf_report(
            design=design,
            requirements=req_dict,
            comparison=comparison,
            comparison_summary="Balanced tier recommended for the given budget constraints.",
        )
        assert pdf_bytes[:4] == b"%PDF"
        assert len(pdf_bytes) > 5000

    def test_pdf_with_diagram_b64(self, hospital_result):
        """PDF with a base64-encoded PNG diagram embeds the image correctly."""
        from app.exporters.pdf_report import generate_pdf_report
        from app.exporters.diagram_image import generate_diagram_png
        import base64

        design, req = hospital_result
        req_dict = req.model_dump()

        # Generate a real diagram PNG and pass it as b64
        png_bytes = generate_diagram_png(design.graph, title="Hospital Network")
        png_b64 = base64.b64encode(png_bytes).decode()

        pdf_bytes = generate_pdf_report(
            design=design,
            requirements=req_dict,
            diagram_png_b64=png_b64,
        )
        assert pdf_bytes[:4] == b"%PDF"
        assert len(pdf_bytes) > 10000  # Should be larger with embedded image

    def test_pdf_all_variants(self):
        """PDF generates for all three variants."""
        from app.schemas.requirements import RequirementsInput
        from app.engine.pipeline import run_pipeline
        from app.exporters.pdf_report import generate_pdf_report

        req_path = SCENARIO_DIR / "school.json"
        req = RequirementsInput.model_validate_json(req_path.read_text(encoding="utf-8"))
        req_dict = req.model_dump()

        for variant in ["budget", "balanced", "high_performance"]:
            design = run_pipeline(req, variant=variant)
            pdf_bytes = generate_pdf_report(design=design, requirements=req_dict)
            assert pdf_bytes[:4] == b"%PDF", f"PDF failed for variant {variant}"


# ── Diagram Image Tests ───────────────────────────────────────────────────────

class TestDiagramImage:
    """Test the static NetworkX/Matplotlib diagram renderer."""

    def test_diagram_generates_png(self, hospital_result):
        """generate_diagram_png returns valid PNG bytes."""
        from app.exporters.diagram_image import generate_diagram_png
        design, _ = hospital_result
        png_bytes = generate_diagram_png(design.graph, title="Test Diagram")
        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 1000
        # PNG files start with the PNG signature
        assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"

    def test_diagram_empty_graph(self):
        """Empty graph produces a placeholder PNG without crashing."""
        from app.exporters.diagram_image import generate_diagram_png
        png_bytes = generate_diagram_png({"nodes": [], "edges": []})
        assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"

    def test_diagram_all_scenarios(self):
        """Diagram renders for all four scenarios."""
        from app.schemas.requirements import RequirementsInput
        from app.engine.pipeline import run_pipeline
        from app.exporters.diagram_image import generate_diagram_png

        for scenario_name in ["small_office", "school", "hospital", "it_company"]:
            scenario_path = SCENARIO_DIR / f"{scenario_name}.json"
            req = RequirementsInput.model_validate_json(scenario_path.read_text(encoding="utf-8"))
            design = run_pipeline(req, variant="balanced")
            assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n", f"PNG signature missing for {scenario_name}"
            assert len(png_bytes) > 1000, f"PNG too small for {scenario_name}"

    def test_export_diagram_png_api(self, hospital_result):
        """POST /api/export/diagram-png returns a valid PNG response."""
        from fastapi.testclient import TestClient
        from app.main import app

        design, _ = hospital_result
        client = TestClient(app)
        res = client.post("/api/export/diagram-png", json={"design": design.model_dump()})
        assert res.status_code == 200
        assert res.headers["content-type"] == "image/png"
        assert res.content[:8] == b"\x89PNG\r\n\x1a\n"


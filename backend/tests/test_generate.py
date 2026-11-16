"""Tests for the One-Click llms.txt + JSON-LD Generator feature.

These tests verify:
  - scanner.generate_llms_txt(result) and scanner.generate_json_ld(result)
    are public functions that accept a scan result dict.
  - reports.generate_llms_txt_file(result) and reports.generate_json_ld_file(result)
    return (filename, content) tuples suitable for download.
  - POST /api/generate/llms-txt and POST /api/generate/json-ld endpoints
    exist, accept a scan result JSON body, and return downloadable files.
"""
import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# ---------------------------------------------------------------------------
# Fixtures: a realistic scan result dict
# ---------------------------------------------------------------------------

def _make_scan_result():
    """Build a minimal but complete scan result dict as returned by /api/scan."""
    return {
        "url": "https://acme.example.com",
        "score": 55,
        "checks": [
            {
                "check": "llms.txt File",
                "key": "llms_txt",
                "status": "fail",
                "points_earned": 0,
                "points_max": 15,
                "points_lost": 15,
                "detail": "No llms.txt found at /llms.txt.",
                "action": "Create /llms.txt at your site root.",
                "effort_level": "Easy",
                "effort_time": "1 hour",
            },
            {
                "check": "Structured Data (JSON-LD / Schema.org)",
                "key": "structured_data",
                "status": "fail",
                "points_earned": 0,
                "points_max": 20,
                "points_lost": 20,
                "detail": "No JSON-LD or microdata found.",
                "action": "Add JSON-LD structured data to your pages.",
                "effort_level": "Medium",
                "effort_time": "2-4 hours",
            },
            {
                "check": "AI Crawler Access",
                "key": "ai_crawler_access",
                "status": "pass",
                "points_earned": 20,
                "points_max": 20,
                "points_lost": 0,
                "detail": "Robots.txt allows AI crawlers.",
                "action": "No action needed.",
                "effort_level": "Easy",
                "effort_time": "0 min",
            },
        ],
        "recommendations": [
            {"key": "structured_data", "status": "fail", "points_lost": 20},
            {"key": "llms_txt", "status": "fail", "points_lost": 15},
        ],
        "subpages": {
            "pricing": {
                "url": "https://acme.example.com/pricing",
                "pricing_parsability": {"pass": True, "detail": "Pricing visible."},
                "js_rendering": {"pass": True, "detail": "Server-rendered."},
            },
            "docs": {
                "url": "https://acme.example.com/docs",
                "structured_data": {"pass": False, "detail": "No structured data."},
                "js_rendering": {"pass": True, "detail": "Server-rendered."},
            },
            "contact": {
                "url": "https://acme.example.com/contact",
                "contact_parsability": {"pass": True, "detail": "Contact email found."},
            },
        },
        "llms_txt_template": None,
        "json_ld_snippet": None,
        "next_step": {
            "key": "structured_data",
            "points_gain": 20,
            "workflow": "Add JSON-LD to your homepage.",
        },
    }


# ---------------------------------------------------------------------------
# 1. scanner.generate_llms_txt (public function)
# ---------------------------------------------------------------------------

class TestScannerGenerateLlmsTxt:
    """The scanner module must expose a public generate_llms_txt(result) function."""

    def test_function_exists(self):
        import scanner
        assert hasattr(scanner, "generate_llms_txt"), (
            "scanner.generate_llms_txt is not defined. The private _generate_llms_txt_template "
            "should be exposed as a public function that takes a scan result dict."
        )

    def test_returns_string(self):
        import scanner
        result = _make_scan_result()
        content = scanner.generate_llms_txt(result)
        assert isinstance(content, str)
        assert len(content) > 0

    def test_contains_company_name(self):
        import scanner
        result = _make_scan_result()
        content = scanner.generate_llms_txt(result)
        # Company name is derived from the URL domain when no title is available
        assert "acme" in content.lower() or "acme.example.com" in content.lower()

    def test_contains_key_pages_section(self):
        import scanner
        result = _make_scan_result()
        content = scanner.generate_llms_txt(result)
        assert "Key Pages" in content or "key pages" in content.lower()

    def test_contains_subpage_urls(self):
        import scanner
        result = _make_scan_result()
        content = scanner.generate_llms_txt(result)
        assert "https://acme.example.com/pricing" in content
        assert "https://acme.example.com/docs" in content
        assert "https://acme.example.com/contact" in content

    def test_contains_for_automated_tools_section(self):
        import scanner
        result = _make_scan_result()
        content = scanner.generate_llms_txt(result)
        assert "For Automated Tools" in content

    def test_has_h1_header(self):
        import scanner
        result = _make_scan_result()
        content = scanner.generate_llms_txt(result)
        assert content.startswith("# ")

    def test_empty_subpages_still_works(self):
        import scanner
        result = _make_scan_result()
        result["subpages"] = {}
        content = scanner.generate_llms_txt(result)
        assert isinstance(content, str)
        assert len(content) > 0


# ---------------------------------------------------------------------------
# 2. scanner.generate_json_ld (public function)
# ---------------------------------------------------------------------------

class TestScannerGenerateJsonLd:
    """The scanner module must expose a public generate_json_ld(result) function."""

    def test_function_exists(self):
        import scanner
        assert hasattr(scanner, "generate_json_ld"), (
            "scanner.generate_json_ld is not defined. The private _generate_json_ld_snippet "
            "should be exposed as a public function that takes a scan result dict."
        )

    def test_returns_valid_json(self):
        import scanner
        result = _make_scan_result()
        content = scanner.generate_json_ld(result)
        parsed = json.loads(content)
        assert isinstance(parsed, dict)

    def test_has_schema_org_context(self):
        import scanner
        result = _make_scan_result()
        content = scanner.generate_json_ld(result)
        parsed = json.loads(content)
        assert parsed.get("@context") == "https://schema.org"

    def test_has_organization_block(self):
        import scanner
        result = _make_scan_result()
        content = scanner.generate_json_ld(result)
        parsed = json.loads(content)
        graph = parsed.get("@graph", [])
        types = [node.get("@type") for node in graph]
        assert "Organization" in types

    def test_has_software_application_block(self):
        import scanner
        result = _make_scan_result()
        content = scanner.generate_json_ld(result)
        parsed = json.loads(content)
        graph = parsed.get("@graph", [])
        types = [node.get("@type") for node in graph]
        assert "SoftwareApplication" in types

    def test_has_faq_page_block(self):
        import scanner
        result = _make_scan_result()
        content = scanner.generate_json_ld(result)
        parsed = json.loads(content)
        graph = parsed.get("@graph", [])
        types = [node.get("@type") for node in graph]
        assert "FAQPage" in types

    def test_organization_has_url(self):
        import scanner
        result = _make_scan_result()
        content = scanner.generate_json_ld(result)
        parsed = json.loads(content)
        org = next(n for n in parsed["@graph"] if n.get("@type") == "Organization")
        assert org.get("url") == "https://acme.example.com"

    def test_empty_subpages_still_valid(self):
        import scanner
        result = _make_scan_result()
        result["subpages"] = {}
        content = scanner.generate_json_ld(result)
        parsed = json.loads(content)
        assert parsed.get("@context") == "https://schema.org"


# ---------------------------------------------------------------------------
# 3. reports.generate_llms_txt_file and generate_json_ld_file (download helpers)
# ---------------------------------------------------------------------------

class TestReportsGenerateFiles:
    """The reports module must expose generate_llms_txt_file and generate_json_ld_file."""

    def test_generate_llms_txt_file_exists(self):
        import reports
        assert hasattr(reports, "generate_llms_txt_file"), (
            "reports.generate_llms_txt_file is not defined."
        )

    def test_generate_json_ld_file_exists(self):
        import reports
        assert hasattr(reports, "generate_json_ld_file"), (
            "reports.generate_json_ld_file is not defined."
        )

    def test_llms_txt_file_returns_tuple(self):
        import reports
        result = _make_scan_result()
        filename, content = reports.generate_llms_txt_file(result)
        assert isinstance(filename, str)
        assert isinstance(content, str)
        assert filename.endswith(".txt")

    def test_llms_txt_filename_includes_domain(self):
        import reports
        result = _make_scan_result()
        filename, _ = reports.generate_llms_txt_file(result)
        assert "acme" in filename

    def test_json_ld_file_returns_tuple(self):
        import reports
        result = _make_scan_result()
        filename, content = reports.generate_json_ld_file(result)
        assert isinstance(filename, str)
        assert isinstance(content, str)
        assert filename.endswith(".json")

    def test_json_ld_content_is_valid_json(self):
        import reports
        result = _make_scan_result()
        _, content = reports.generate_json_ld_file(result)
        parsed = json.loads(content)
        assert "@context" in parsed


# ---------------------------------------------------------------------------
# 4. API endpoints: POST /api/generate/llms-txt and POST /api/generate/json-ld
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


class TestGenerateLlmsTxtEndpoint:
    """POST /api/generate/llms-txt accepts a scan result and returns a file."""

    def test_endpoint_exists(self, client):
        resp = client.post("/api/generate/llms-txt", json=_make_scan_result())
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}. "
            "The endpoint POST /api/generate/llms-txt does not exist."
        )

    def test_returns_text_content_type(self, client):
        resp = client.post("/api/generate/llms-txt", json=_make_scan_result())
        assert resp.status_code == 200
        assert "text/plain" in resp.headers.get("content-type", "")

    def test_returns_content_disposition(self, client):
        resp = client.post("/api/generate/llms-txt", json=_make_scan_result())
        assert resp.status_code == 200
        cd = resp.headers.get("content-disposition", "")
        assert "attachment" in cd
        assert ".txt" in cd

    def test_body_contains_company(self, client):
        resp = client.post("/api/generate/llms-txt", json=_make_scan_result())
        assert resp.status_code == 200
        assert "acme" in resp.text.lower()

    def test_body_has_h1(self, client):
        resp = client.post("/api/generate/llms-txt", json=_make_scan_result())
        assert resp.status_code == 200
        assert resp.text.startswith("# ")

    def test_rejects_empty_body(self, client):
        resp = client.post("/api/generate/llms-txt", json={})
        assert resp.status_code in (400, 422)


class TestGenerateJsonLdEndpoint:
    """POST /api/generate/json-ld accepts a scan result and returns a file."""

    def test_endpoint_exists(self, client):
        resp = client.post("/api/generate/json-ld", json=_make_scan_result())
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}. "
            "The endpoint POST /api/generate/json-ld does not exist."
        )

    def test_returns_json_content_type(self, client):
        resp = client.post("/api/generate/json-ld", json=_make_scan_result())
        assert resp.status_code == 200
        ct = resp.headers.get("content-type", "")
        assert "application/json" in ct or "ld+json" in ct

    def test_returns_content_disposition(self, client):
        resp = client.post("/api/generate/json-ld", json=_make_scan_result())
        assert resp.status_code == 200
        cd = resp.headers.get("content-disposition", "")
        assert "attachment" in cd
        assert ".json" in cd

    def test_body_is_valid_json(self, client):
        resp = client.post("/api/generate/json-ld", json=_make_scan_result())
        assert resp.status_code == 200
        parsed = json.loads(resp.text)
        assert "@context" in parsed
        assert "@graph" in parsed

    def test_rejects_empty_body(self, client):
        resp = client.post("/api/generate/json-ld", json={})
        assert resp.status_code in (400, 422)

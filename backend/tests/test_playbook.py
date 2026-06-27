"""Tests for the playbook module."""
import pytest
from playbook import get_recommendation, get_recommendations_for_result, PLAYBOOK


class TestGetRecommendation:
    """Tests for get_recommendation function."""
    
    def test_ai_crawler_access(self):
        """Test recommendation for ai_crawler_access check."""
        rec = get_recommendation("ai_crawler_access")
        assert isinstance(rec, dict)
        assert "recommendation" in rec
        assert isinstance(rec["recommendation"], str)
        assert len(rec["recommendation"]) > 0
    
    def test_llms_txt(self):
        """Test recommendation for llms_txt check."""
        rec = get_recommendation("llms_txt")
        assert isinstance(rec, dict)
        assert "recommendation" in rec
        assert "llms.txt" in rec["recommendation"].lower()
    
    def test_structured_data(self):
        """Test recommendation for structured_data check."""
        rec = get_recommendation("structured_data")
        assert isinstance(rec, dict)
        assert "recommendation" in rec
        assert "json" in rec["recommendation"].lower() or "schema" in rec["recommendation"].lower()
    
    def test_js_rendering(self):
        """Test recommendation for js_rendering check."""
        rec = get_recommendation("js_rendering")
        assert isinstance(rec, dict)
        assert "recommendation" in rec
        assert "server" in rec["recommendation"].lower() or "render" in rec["recommendation"].lower()
    
    def test_pricing_parsability(self):
        """Test recommendation for pricing_parsability check."""
        rec = get_recommendation("pricing_parsability")
        assert isinstance(rec, dict)
        assert "recommendation" in rec
        assert "price" in rec["recommendation"].lower() or "offer" in rec["recommendation"].lower()
    
    def test_contact_parsability(self):
        """Test recommendation for contact_parsability check."""
        rec = get_recommendation("contact_parsability")
        assert isinstance(rec, dict)
        assert "recommendation" in rec
        assert "contact" in rec["recommendation"].lower()
    
    def test_api_discoverability(self):
        """Test recommendation for api_discoverability check."""
        rec = get_recommendation("api_discoverability")
        assert isinstance(rec, dict)
        assert "recommendation" in rec
        assert "api" in rec["recommendation"].lower() or "openapi" in rec["recommendation"].lower()
    
    def test_sitemap(self):
        """Test recommendation for sitemap check."""
        rec = get_recommendation("sitemap")
        assert isinstance(rec, dict)
        assert "recommendation" in rec
        assert "sitemap" in rec["recommendation"].lower()
    
    def test_cookie_consent_wall(self):
        """Test recommendation for cookie_consent_wall check."""
        rec = get_recommendation("cookie_consent_wall")
        assert isinstance(rec, dict)
        assert "recommendation" in rec
        assert "cookie" in rec["recommendation"].lower()
    
    def test_content_freshness(self):
        """Test recommendation for content_freshness check."""
        rec = get_recommendation("content_freshness")
        assert isinstance(rec, dict)
        assert "recommendation" in rec
        assert "cache" in rec["recommendation"].lower() or "freshness" in rec["recommendation"].lower()
    
    def test_auth_wall(self):
        """Test recommendation for auth_wall check."""
        rec = get_recommendation("auth_wall")
        assert isinstance(rec, dict)
        assert "recommendation" in rec
        assert "auth" in rec["recommendation"].lower() or "login" in rec["recommendation"].lower()
    
    def test_mcp_discoverability(self):
        """Test recommendation for mcp_discoverability check."""
        rec = get_recommendation("mcp_discoverability")
        assert isinstance(rec, dict)
        assert "recommendation" in rec
        assert "mcp" in rec["recommendation"].lower()
    
    def test_unknown_check(self):
        """Test recommendation for unknown check key."""
        rec = get_recommendation("unknown_check_key")
        assert isinstance(rec, dict)
        assert "recommendation" in rec


class TestGetRecommendationsForResult:
    """Tests for get_recommendations_for_result function."""
    
    def test_empty_result(self):
        """Test with empty result."""
        result = {"checks": [], "score": 100}
        recommendations = get_recommendations_for_result(result)
        assert recommendations == []
    
    def test_pass_checks_no_recommendations(self):
        """Test that passing checks don't generate recommendations."""
        result = {
            "checks": [
                {"key": "ai_crawler_access", "status": "pass", "points_lost": 0},
            ],
            "score": 100,
        }
        recommendations = get_recommendations_for_result(result)
        assert recommendations == []
    
    def test_fail_checks_generate_recommendations(self):
        """Test that failing checks generate recommendations."""
        result = {
            "checks": [
                {"key": "llms_txt", "status": "fail", "points_lost": 15},
                {"key": "structured_data", "status": "fail", "points_lost": 20},
            ],
            "score": 50,
        }
        recommendations = get_recommendations_for_result(result)
        assert len(recommendations) == 2
        assert all("recommendation" in rec for rec in recommendations)
        assert all("effort" in rec for rec in recommendations)
    
    def test_warning_checks_generate_recommendations(self):
        """Test that warning checks generate recommendations."""
        result = {
            "checks": [
                {"key": "js_rendering", "status": "warning", "points_lost": 7},
            ],
            "score": 70,
        }
        recommendations = get_recommendations_for_result(result)
        assert len(recommendations) == 1
        assert recommendations[0]["status"] == "warning"
    
    def test_mixed_status_checks(self):
        """Test mixed pass/fail/warning checks."""
        result = {
            "checks": [
                {"key": "ai_crawler_access", "status": "pass", "points_lost": 0},
                {"key": "llms_txt", "status": "fail", "points_lost": 15},
                {"key": "structured_data", "status": "warning", "points_lost": 10},
            ],
            "score": 65,
        }
        recommendations = get_recommendations_for_result(result)
        assert len(recommendations) == 2  # Only fail and warning
        pass_checks = [rec for rec in recommendations if rec["status"] != "pass"]
        assert len(pass_checks) == 2


class TestPlaybookConstants:
    """Tests for PLAYBOOK dictionary."""
    
    def test_all_checks_have_recommendations(self):
        """Test that all defined checks have recommendations."""
        for check_key in PLAYBOOK.keys():
            rec = get_recommendation(check_key)
            assert isinstance(rec, dict), f"Recommendation for {check_key} is not a dict"
            assert "recommendation" in rec, f"No recommendation for {check_key}"
            assert len(rec["recommendation"]) > 0, f"Empty recommendation for {check_key}"
    
    def test_playbook_has_research_sources(self):
        """Test that playbook entries have research sources."""
        for check_key, rec in PLAYBOOK.items():
            assert "research_source" in rec, f"Missing research_source for {check_key}"
            assert "url" in rec, f"Missing url for {check_key}"
    
    def test_playbook_has_effort_estimates(self):
        """Test that playbook entries have effort estimates."""
        for check_key, rec in PLAYBOOK.items():
            assert "effort" in rec, f"Missing effort for {check_key}"
            assert "time" in rec, f"Missing time for {check_key}"

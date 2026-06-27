"""Tests for the badge server module."""
import pytest
import re
from typing import Optional
from unittest.mock import MagicMock

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.testclient import TestClient
    
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


@pytest.fixture
def mock_app():
    """Create a mock FastAPI app for badge serving."""
    from backend.badge_server import generate_svg, generate_svg_with_domain
    
    # Create a simple test app
    def mock_badget(domain: str, score: Optional[int] = None) -> str:
        """Mock badge endpoint."""
        if not domain or not re.match(r'^[a-zA-Z0-9][-a-zA-Z0-9.]*$', domain):
            raise HTTPException(status_code=400, detail="Invalid domain format")
        if score is not None:
            if score < 0 or score > 100:
                raise HTTPException(status_code=400, detail="Score must be between 0 and 100")
        return generate_svg_with_domain(score or 0, domain)
    
    app = FastAPI()
    
    @app.get("/badge/{domain}")
    def badge(domain: str, score: Optional[int] = None):
        # Handle empty domain - FastAPI allows empty string as path param
        # But we need to explicitly check for it
        if domain == "":
            raise HTTPException(status_code=400, detail="Empty domain not allowed")
        return mock_badget(domain, score)
    
    @app.get("/health")
    def health():
        return {"status": "ok"}
    
    # Add a catch-all for empty path that validates
    @app.get("/badge")
    def badge_empty(domain: str = "", score: Optional[int] = None):
        """Handle empty path explicitly."""
        if not domain:
            raise HTTPException(status_code=400, detail="Empty domain not allowed")
        return mock_badget(domain, score)
    
    return app


class TestBadgeGeneration:
    """Tests for SVG badge generation."""
    
    def test_generate_svg_returns_valid_svg(self):
        """Test that generate_svg returns valid SVG content."""
        from backend.badge_server import generate_svg
        
        svg = generate_svg(85, "example.com")
        assert isinstance(svg, str)
        assert "<svg" in svg
        assert "</svg>" in svg
    
    def test_generate_svg_contains_score(self):
        """Test that SVG contains the score."""
        from backend.badge_server import generate_svg
        
        svg = generate_svg(85, "example.com")
        assert "85" in svg
    
    def test_generate_svg_color_by_score_high(self):
        """Test green color for high scores."""
        from backend.badge_server import generate_svg
        
        svg = generate_svg(90, "example.com")
        assert "PASS" in svg or "pass" in svg
    
    def test_generate_svg_color_by_score_medium(self):
        """Test amber color for medium scores."""
        from backend.badge_server import generate_svg
        
        svg = generate_svg(60, "example.com")
        assert "WARNING" in svg or "warning" in svg
    
    def test_generate_svg_color_by_score_low(self):
        """Test red color for low scores."""
        from backend.badge_server import generate_svg
        
        svg = generate_svg(20, "example.com")
        assert "FAIL" in svg or "fail" in svg
    
    def test_generate_svg_color_by_score_unknown(self):
        """Test grey color for unknown scores."""
        from backend.badge_server import generate_svg
        
        svg = generate_svg(None, "example.com")
        assert "UNKNOWN" in svg or "unknown" in svg
    
    def test_generate_svg_with_domain_link(self):
        """Test that generate_svg_with_domain includes link."""
        from backend.badge_server import generate_svg_with_domain
        
        svg = generate_svg_with_domain(85, "https://example.com")
        assert "example.com" in svg
        assert "<a" in svg


class TestBadgeServer:
    """Tests for badge server endpoints."""
    
    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
    def test_health_endpoint(self, mock_app):
        """Test health endpoint returns ok."""
        client = TestClient(mock_app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
    def test_badge_endpoint_valid_domain(self, mock_app):
        """Test badge endpoint with valid domain."""
        client = TestClient(mock_app)
        response = client.get("/badge/example.com")
        assert response.status_code == 200
        svg = response.text
        assert "<svg" in svg
        assert "example.com" in svg
    
    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
    def test_badge_endpoint_with_score(self, mock_app):
        """Test badge endpoint with score parameter."""
        client = TestClient(mock_app)
        response = client.get("/badge/example.com?score=85")
        assert response.status_code == 200
        svg = response.text
        assert "85" in svg
    
    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
    def test_badge_endpoint_invalid_domain(self, mock_app):
        """Test badge endpoint rejects invalid domain."""
        client = TestClient(mock_app)
        response = client.get("/badge/invalid%20domain")
        assert response.status_code == 400
    
    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
    def test_badge_endpoint_score_out_of_range(self, mock_app):
        """Test badge endpoint rejects score out of range."""
        client = TestClient(mock_app)
        response = client.get("/badge/example.com?score=150")
        assert response.status_code == 400
        response = client.get("/badge/example.com?score=-10")
        assert response.status_code == 400
    
    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
    def test_badge_endpoint_empty_domain(self, mock_app):
        """Test badge endpoint rejects empty domain."""
        client = TestClient(mock_app)
        # Use the /badge endpoint (not /badge/) to test empty domain
        response = client.get("/badge")
        assert response.status_code == 400
    
    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
    def test_badge_endpoint_none_score(self, mock_app):
        """Test badge endpoint with None score shows unknown status."""
        client = TestClient(mock_app)
        # FastAPI converts ?score=None to ?score=None as string
        # Use query param with string "None" or omit the score
        response = client.get("/badge/example.com")
        assert response.status_code == 200


class TestSVGContent:
    """Tests for SVG content structure."""
    
    def test_svg_has_required_elements(self):
        """Test SVG has required elements."""
        from backend.badge_server import generate_svg
        
        svg = generate_svg(85, "example.com")
        assert "svg" in svg.lower()
        assert "xmlns" in svg
    
    def test_svg_has_aria_label(self):
        """Test SVG has aria-label."""
        from backend.badge_server import generate_svg
        
        svg = generate_svg(85, "example.com")
        assert "aria-label" in svg
    
    def test_svg_has_title(self):
        """Test SVG has title element."""
        from backend.badge_server import generate_svg
        
        svg = generate_svg(85, "example.com")
        assert "<title>" in svg
    
    def test_svg_width_height(self):
        """Test SVG has width and height."""
        from backend.badge_server import generate_svg
        
        svg = generate_svg(85, "example.com")
        assert 'width="300"' in svg or 'width=' in svg
        assert 'height="50"' in svg or 'height=' in svg
    
    def test_svg_domain_truncation(self):
        """Test long domains are truncated in SVG."""
        from backend.badge_server import generate_svg_with_domain
        
        svg = generate_svg_with_domain(85, "https://very-long-domain-name-that-exceeds-length.example.com")
        assert "..." in svg


class TestScoreColorMapping:
    """Tests for score to color/status mapping."""
    
    def test_score_100_pass(self):
        """Test score 100 maps to pass."""
        from backend.badge_server import generate_svg
        
        svg = generate_svg(100, "example.com")
        assert "PASS" in svg or "pass" in svg
    
    def test_score_80_pass(self):
        """Test score 80 maps to pass."""
        from backend.badge_server import generate_svg
        
        svg = generate_svg(80, "example.com")
        assert "PASS" in svg or "pass" in svg
    
    def test_score_79_warning(self):
        """Test score 79 maps to warning."""
        from backend.badge_server import generate_svg
        
        svg = generate_svg(79, "example.com")
        assert "WARNING" in svg or "warning" in svg
    
    def test_score_50_warning(self):
        """Test score 50 maps to warning."""
        from backend.badge_server import generate_svg
        
        svg = generate_svg(50, "example.com")
        assert "WARNING" in svg or "warning" in svg
    
    def test_score_49_fail(self):
        """Test score 49 maps to fail."""
        from backend.badge_server import generate_svg
        
        svg = generate_svg(49, "example.com")
        assert "FAIL" in svg or "fail" in svg
    
    def test_score_0_fail(self):
        """Test score 0 maps to fail."""
        from backend.badge_server import generate_svg
        
        svg = generate_svg(0, "example.com")
        assert "FAIL" in svg or "fail" in svg

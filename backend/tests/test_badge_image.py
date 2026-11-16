"""Tests for the badge image endpoint (GET /badge/{domain}/image).

Reproduces the bug where `badge_image` in `backend/badge_server.py` is
annotated `-> bytes` but returns a 2-tuple
(`content.encode("utf-8"), "image/svg+xml"`). FastAPI serializes the tuple
and validates it against the `bytes` return annotation, raising
`fastapi.exceptions.ResponseValidationError`, so EVERY request to
`/badge/{domain}/image` returns 500 Internal Server Error.

The approved fix makes the handler return a proper `Response` object
(`Response(content=..., media_type="image/svg+xml")`). These tests assert
the endpoint returns 200 with an SVG body and the image/svg+xml content type
for a valid domain. They FAIL on the current (unfixed) code (500) and PASS
once the handler returns a real Response.
"""
import pytest

try:
    from fastapi.testclient import TestClient

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


@pytest.fixture
def badge_client():
    """Test client for the real badge app (the module under test)."""
    from backend.badge_server import make_badge_app

    # raise_server_exceptions=False so a FastAPI ResponseValidationError
    # surfaces as a 500 response (the observed bug) instead of propagating
    # out of the test client.
    return TestClient(make_badge_app(), raise_server_exceptions=False)


class TestBadgeImageEndpoint:
    """Tests for GET /badge/{domain}/image."""

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
    def test_image_returns_200_for_valid_domain(self, badge_client):
        """A valid domain must return 200, not 500."""
        response = badge_client.get("/badge/example.com/image?score=85")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: "
            f"{response.text[:80]!r}"
        )

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
    def test_image_content_type_is_svg(self, badge_client):
        """The image endpoint must be served as image/svg+xml."""
        response = badge_client.get("/badge/example.com/image?score=85")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: "
            f"{response.text[:80]!r}"
        )
        assert "image/svg+xml" in response.headers.get("content-type", "")

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
    def test_image_body_is_svg(self, badge_client):
        """The response body must be the generated SVG."""
        response = badge_client.get("/badge/example.com/image?score=85")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: "
            f"{response.text[:80]!r}"
        )
        body = response.content.decode("utf-8")
        assert "<svg" in body
        assert "</svg>" in body
        assert "85" in body

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
    def test_image_without_score_returns_200(self, badge_client):
        """Omitting the score must also return 200 (not 500)."""
        response = badge_client.get("/badge/example.com/image")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: "
            f"{response.text[:80]!r}"
        )

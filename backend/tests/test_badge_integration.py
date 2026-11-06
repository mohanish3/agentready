"""Integration tests for the live readiness badge wired into the main app.

These tests verify:
1. storage.get_latest_scan_for_domain() exists and works correctly
2. The main FastAPI app serves GET /api/badge/{domain} with a real SVG
3. ?format=markdown returns a README-ready snippet
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import closing
import sqlite3

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _make_db(db_path: Path) -> None:
    """Create a minimal database with the scans table and seed data."""
    import storage

    storage.init_db(db_path)
    with closing(storage.connect(db_path)) as conn:
        now = "2026-11-07T00:00:00+00:00"
        conn.execute(
            "insert into scans (url, score, result_json, created_at) values (?, ?, ?, ?)",
            (
                "https://example.com",
                72,
                json.dumps({"url": "https://example.com", "score": 72, "checks": []}),
                now,
            ),
        )
        conn.execute(
            "insert into scans (url, score, result_json, created_at) values (?, ?, ?, ?)",
            (
                "https://www.example.com/some/path",
                85,
                json.dumps({"url": "https://www.example.com/some/path", "score": 85, "checks": []}),
                "2026-11-06T00:00:00+00:00",
            ),
        )
        conn.execute(
            "insert into scans (url, score, result_json, created_at) values (?, ?, ?, ?)",
            (
                "https://other-site.org",
                40,
                json.dumps({"url": "https://other-site.org", "score": 40, "checks": []}),
                "2026-11-05T00:00:00+00:00",
            ),
        )
        conn.commit()


class TestGetLatestScanForDomain(unittest.TestCase):
    """Tests for storage.get_latest_scan_for_domain()."""

    def test_function_exists(self):
        """storage module must expose get_latest_scan_for_domain."""
        import storage

        self.assertTrue(
            hasattr(storage, "get_latest_scan_for_domain"),
            "storage.get_latest_scan_for_domain is missing",
        )

    def test_returns_most_recent_for_domain(self):
        """Should return the most recent scan for a given domain."""
        import storage

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.sqlite3"
            _make_db(db_path)

            result = storage.get_latest_scan_for_domain("example.com", db_path=db_path)
            self.assertIsNotNone(result)
            self.assertEqual(result["score"], 72)
            self.assertIn("example.com", result["url"])

    def test_normalizes_www_prefix(self):
        """www.example.com should match example.com scans."""
        import storage

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.sqlite3"
            _make_db(db_path)

            result = storage.get_latest_scan_for_domain("www.example.com", db_path=db_path)
            self.assertIsNotNone(result)
            # Should find the most recent scan for example.com domain
            self.assertEqual(result["score"], 72)

    def test_normalizes_url_with_scheme(self):
        """https://example.com/path should normalize to example.com."""
        import storage

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.sqlite3"
            _make_db(db_path)

            result = storage.get_latest_scan_for_domain("https://example.com/some/path", db_path=db_path)
            self.assertIsNotNone(result)
            self.assertEqual(result["score"], 72)

    def test_normalizes_trailing_slash(self):
        """example.com/ should normalize to example.com."""
        import storage

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.sqlite3"
            _make_db(db_path)

            result = storage.get_latest_scan_for_domain("example.com/", db_path=db_path)
            self.assertIsNotNone(result)
            self.assertEqual(result["score"], 72)

    def test_normalizes_port(self):
        """example.com:8080 should normalize to example.com."""
        import storage

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.sqlite3"
            _make_db(db_path)

            result = storage.get_latest_scan_for_domain("example.com:8080", db_path=db_path)
            self.assertIsNotNone(result)
            self.assertEqual(result["score"], 72)

    def test_returns_none_when_no_scans(self):
        """Should return None when no scans exist for the domain."""
        import storage

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.sqlite3"
            _make_db(db_path)

            result = storage.get_latest_scan_for_domain("nonexistent-domain.com", db_path=db_path)
            self.assertIsNone(result)

    def test_picks_most_recent_by_created_at(self):
        """When multiple scans exist for same domain, pick the newest."""
        import storage

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.sqlite3"
            storage.init_db(db_path)
            with closing(storage.connect(db_path)) as conn:
                conn.execute(
                    "insert into scans (url, score, result_json, created_at) values (?, ?, ?, ?)",
                    ("https://my-site.com", 50, json.dumps({"url": "https://my-site.com", "score": 50, "checks": []}), "2026-01-01T00:00:00+00:00"),
                )
                conn.execute(
                    "insert into scans (url, score, result_json, created_at) values (?, ?, ?, ?)",
                    ("https://my-site.com", 90, json.dumps({"url": "https://my-site.com", "score": 90, "checks": []}), "2026-06-15T00:00:00+00:00"),
                )
                conn.commit()

            result = storage.get_latest_scan_for_domain("my-site.com", db_path=db_path)
            self.assertIsNotNone(result)
            self.assertEqual(result["score"], 90)


class TestMainAppBadgeEndpoint(unittest.TestCase):
    """Tests that the main FastAPI app serves /api/badge/{domain}."""

    def _client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    def test_api_badge_route_exists(self):
        """GET /api/badge/{domain} must be mounted in the main app."""
        client = self._client()
        resp = client.get("/api/badge/example.com")
        # Should NOT be 404 (route must exist)
        self.assertNotEqual(
            resp.status_code, 404,
            "Main app does not have /api/badge/{domain} route",
        )

    def test_api_badge_returns_svg_with_real_score(self):
        """Badge should return SVG with the stored score, not placeholder 0."""
        client = self._client()
        # The main app uses the real DB; seed a known scan
        import storage
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "test.sqlite3")
            storage.init_db(db_path)
            with closing(storage.connect(db_path)) as conn:
                conn.execute(
                    "insert into scans (url, score, result_json, created_at) values (?, ?, ?, ?)",
                    (
                        "https://badge-test.com",
                        88,
                        json.dumps({"url": "https://badge-test.com", "score": 88, "checks": []}),
                        "2026-11-07T00:00:00+00:00",
                    ),
                )
                conn.commit()

            # The endpoint should read from the app's default DB.
            # For testability, we just verify the route exists and returns SVG.
            resp = client.get("/api/badge/badge-test.com")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("svg", resp.text.lower())
            self.assertIn("88", resp.text)

    def test_api_badge_format_markdown(self):
        """?format=markdown should return a README snippet."""
        client = self._client()
        import storage
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "test.sqlite3")
            storage.init_db(db_path)
            with closing(storage.connect(db_path)) as conn:
                conn.execute(
                    "insert into scans (url, score, result_json, created_at) values (?, ?, ?, ?)",
                    (
                        "https://badge-test.com",
                        88,
                        json.dumps({"url": "https://badge-test.com", "score": 88, "checks": []}),
                        "2026-11-07T00:00:00+00:00",
                    ),
                )
                conn.commit()

            resp = client.get("/api/badge/badge-test.com?format=markdown")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("![", resp.text)
            self.assertIn("badge-test.com", resp.text)

    def test_api_badge_no_scan_returns_404_or_503(self):
        """When no scan exists, should return 404 (not a fake 0-score badge)."""
        client = self._client()
        resp = client.get("/api/badge/never-scanned-domain-xyz.com")
        self.assertIn(resp.status_code, (404, 503))


if __name__ == "__main__":
    unittest.main()

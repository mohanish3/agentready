"""Tests for the scan history feature (list saved scans, revisit one).

Covers:
- storage.list_scans(): newest-first summaries with id/url/score/created_at
- GET /api/scans: summary list, default cap of 50, ?limit= support
- GET /api/scans/{id}: full stored result, 404 for missing ids

Tests use a throwaway SQLite database; the real agentready.sqlite3 is never
touched. API tests skip if FastAPI is unavailable (mirrors test_badge_server).
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from fastapi.testclient import TestClient

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


def _sample_result(url: str, score: int) -> dict:
    return {
        "url": url,
        "score": score,
        "checks": [
            {
                "check": "llms.txt File",
                "key": "llms_txt",
                "status": "fail",
                "points_earned": 0,
                "points_max": 15,
                "points_lost": 15,
                "detail": "No llms.txt found.",
                "action": "Create /llms.txt.",
                "effort_level": "Easy",
                "effort_time": "1 hour",
                "research_source": None,
                "confidence": "high",
            }
        ],
        "recommendations": [],
        "subpages": {},
    }


def _save_many(n: int, db_path) -> list:
    import storage

    return [
        storage.save_scan_result(_sample_result(f"https://site{i}.example.com", 40 + i), db_path=db_path)
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# Storage-level tests
# ---------------------------------------------------------------------------


class TestListScans(unittest.TestCase):
    def test_list_scans_returns_newest_first_summaries(self):
        import storage

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "agentready.sqlite3"
            _save_many(3, db_path)
            summaries = storage.list_scans(db_path=db_path)

        self.assertEqual(len(summaries), 3)
        ids = [s["id"] for s in summaries]
        self.assertEqual(ids, sorted(ids, reverse=True), "summaries must be newest-first")
        for s in summaries:
            self.assertIsInstance(s["id"], int)
            self.assertTrue(s["url"].startswith("https://site"))
            self.assertIsInstance(s["score"], int)
            self.assertRegex(s["created_at"], r"^\d{4}-\d{2}-\d{T}\d{2}:\d{2}")

    def test_list_scans_respects_limit(self):
        import storage

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "agentready.sqlite3"
            _save_many(5, db_path)
            summaries = storage.list_scans(limit=2, db_path=db_path)

        self.assertEqual(len(summaries), 2)
        self.assertTrue(all(set(s) == {"id", "url", "score", "created_at"} for s in summaries))

    def test_list_scans_empty_db(self):
        import storage

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "agentready.sqlite3"
            storage.init_db(db_path)
            self.assertEqual(storage.list_scans(db_path=db_path), [])

    def test_list_scans_limit_zero_returns_all(self):
        import storage

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "agentready.sqlite3"
            _save_many(3, db_path)
            self.assertEqual(len(storage.list_scans(limit=0, db_path=db_path)), 3)


# ---------------------------------------------------------------------------
# API-level tests
# ---------------------------------------------------------------------------


@unittest.skipUnless(FASTAPI_AVAILABLE, "FastAPI not available")
class TestListScansApi(unittest.TestCase):
    """Test GET /api/scans endpoints against a throwaway DB."""

    def setUp(self):
        import storage
        import main

        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "agentready.sqlite3"

        # Redirect all DB connections to the temp DB by patching connect.
        original_connect = storage.connect

        def fake_connect(db_path=None, **kw):
            return original_connect(self.db_path)

        self._patcher = patch.object(storage, "connect", side_effect=fake_connect)
        self._patcher.start()
        self.addCleanup(self._patcher.stop)
        self.addCleanup(self.tmp.cleanup)

        # Seed 3 scans into the temp DB (uses the patched connect).
        _save_many(3, self.db_path)
        self.client = TestClient(main.app)

    def test_returns_stored_scans(self):
        resp = self.client.get("/api/scans")
        self.assertEqual(resp.status_code, 200, f"GET /api/scans -> {resp.status_code}")
        summaries = resp.json()
        self.assertEqual(len(summaries), 3)
        urls = {s["url"] for s in summaries}
        self.assertIn("https://site0.example.com", urls)

    def test_default_cap_is_50(self):
        _save_many(55, self.db_path)
        resp = self.client.get("/api/scans")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 50, "default list must be capped at 50")

    def test_limit_query_param(self):
        resp = self.client.get("/api/scans?limit=2")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)

    def test_summary_shape(self):
        resp = self.client.get("/api/scans")
        self.assertEqual(resp.status_code, 200)
        summaries = resp.json()
        self.assertTrue(all(set(s) == {"id", "url", "score", "created_at"} for s in summaries))

    def test_newest_first(self):
        resp = self.client.get("/api/scans")
        self.assertEqual(resp.status_code, 200)
        ids = [s["id"] for s in resp.json()]
        self.assertEqual(ids, sorted(ids, reverse=True))


@unittest.skipUnless(FASTAPI_AVAILABLE, "FastAPI not available")
class TestGetScanApi(unittest.TestCase):
    """Test GET /api/scans/{id} against a throwaway DB."""

    def setUp(self):
        import storage
        import main

        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "agentready.sqlite3"

        original_connect = storage.connect

        def fake_connect(db_path=None, **kw):
            return original_connect(self.db_path)

        self._patcher = patch.object(storage, "connect", side_effect=fake_connect)
        self._patcher.start()
        self.addCleanup(self._patcher.stop)
        self.addCleanup(self.tmp.cleanup)

        _save_many(3, self.db_path)
        self.client = TestClient(main.app)

    def test_returns_full_stored_result(self):
        import storage

        stored = storage.get_scan(1, db_path=self.db_path)
        resp = self.client.get("/api/scans/1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), stored)

    def test_includes_checks(self):
        resp = self.client.get("/api/scans/1")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["url"], "https://site0.example.com")
        self.assertEqual(body["score"], 40)
        self.assertTrue(any(c["key"] == "llms_txt" for c in body["checks"]))

    def test_missing_id_returns_404(self):
        resp = self.client.get("/api/scans/9999")
        self.assertEqual(resp.status_code, 404)

    def test_non_integer_id_rejected(self):
        resp = self.client.get("/api/scans/abc")
        self.assertEqual(resp.status_code, 422)


if __name__ == "__main__":
    unittest.main()

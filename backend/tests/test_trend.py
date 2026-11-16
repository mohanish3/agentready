"""Tests for the Score Trend Indicator feature.

Covers:
  - storage.get_recent_scans_for_url(url, n) query helper
  - GET /api/trend?url=X&n=N endpoint
"""

import json
import sys
import tempfile
import time
from contextlib import closing
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _make_result(url: str, score: int) -> dict:
    """Build a minimal valid scan result dict for storage.save_scan_result."""
    return {
        "url": url,
        "score": score,
        "checks": [
            {
                "key": "llms_txt",
                "check": "llms.txt File",
                "status": "pass" if score >= 50 else "fail",
                "points_earned": score if score >= 50 else 0,
                "points_max": 100,
                "points_lost": 100 - (score if score >= 50 else 0),
                "detail": "test",
            }
        ],
        "recommendations": [],
    }


class TestGetRecentScansForUrl:
    """Tests for storage.get_recent_scans_for_url."""

    def test_returns_last_n_scans_in_chronological_order(self):
        import storage

        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite3"
            url = "https://example.com"

            scores = [50, 60, 70, 80, 90]
            for s in scores:
                storage.save_scan_result(_make_result(url, s), db_path=db)
                time.sleep(0.01)  # ensure distinct timestamps

            recent = storage.get_recent_scans_for_url(url, n=3, db_path=db)
            assert len(recent) == 3
            # oldest first (chronological)
            assert [r["score"] for r in recent] == [70, 80, 90]

    def test_returns_empty_list_when_no_scans(self):
        import storage

        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite3"
            storage.init_db(db)
            recent = storage.get_recent_scans_for_url("https://nonexistent.example", n=5, db_path=db)
            assert recent == []

    def test_filters_by_url(self):
        import storage

        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite3"
            storage.save_scan_result(_make_result("https://a.example", 50), db_path=db)
            storage.save_scan_result(_make_result("https://b.example", 80), db_path=db)
            storage.save_scan_result(_make_result("https://a.example", 60), db_path=db)

            recent = storage.get_recent_scans_for_url("https://a.example", n=5, db_path=db)
            assert len(recent) == 2
            assert all(r["url"] == "https://a.example" for r in recent)
            assert [r["score"] for r in recent] == [50, 60]

    def test_respects_n_limit(self):
        import storage

        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite3"
            url = "https://example.com"
            for s in [10, 20, 30, 40, 50, 60, 70]:
                storage.save_scan_result(_make_result(url, s), db_path=db)

            recent = storage.get_recent_scans_for_url(url, n=3, db_path=db)
            assert len(recent) == 3
            assert [r["score"] for r in recent] == [50, 60, 70]

    def test_returns_score_url_created_at_fields(self):
        import storage

        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite3"
            url = "https://example.com"
            storage.save_scan_result(_make_result(url, 55), db_path=db)

            recent = storage.get_recent_scans_for_url(url, n=5, db_path=db)
            assert len(recent) == 1
            entry = recent[0]
            assert entry["url"] == url
            assert entry["score"] == 55
            assert "created_at" in entry


class TestTrendEndpoint:
    """Tests for GET /api/trend endpoint."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        import main

        return TestClient(main.app)

    def test_trend_returns_time_series(self, client):
        import storage

        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite3"
            url = "https://example.com"
            scores = [50, 62, 74]
            for s in scores:
                storage.save_scan_result(_make_result(url, s), db_path=db)

            # Point the app at our temp DB
            with _patch_db(db):
                res = client.get("/api/trend", params={"url": url, "n": 5})
                assert res.status_code == 200
                data = res.json()
                assert data["url"] == url
                assert len(data["scores"]) == 3
                assert data["scores"] == [50, 62, 74]

    def test_trend_empty_when_no_scans(self, client):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite3"
            with _patch_db(db):
                res = client.get("/api/trend", params={"url": "https://nope.example", "n": 5})
                assert res.status_code == 200
                data = res.json()
                assert data["url"] == "https://nope.example"
                assert data["scores"] == []
                assert data["delta"] is None

    def test_trend_computes_delta(self, client):
        import storage

        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite3"
            url = "https://example.com"
            # scores: 50, 62, 74  -> delta = 74 - 62 = +12
            for s in [50, 62, 74]:
                storage.save_scan_result(_make_result(url, s), db_path=db)

            with _patch_db(db):
                res = client.get("/api/trend", params={"url": url, "n": 5})
                assert res.status_code == 200
                data = res.json()
                assert data["delta"] == 12

    def test_trend_negative_delta(self, client):
        import storage

        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite3"
            url = "https://example.com"
            # scores: 80, 70, 65  -> delta = 65 - 70 = -5
            for s in [80, 70, 65]:
                storage.save_scan_result(_make_result(url, s), db_path=db)

            with _patch_db(db):
                res = client.get("/api/trend", params={"url": url, "n": 5})
                assert res.status_code == 200
                data = res.json()
                assert data["delta"] == -5

    def test_trend_flat_when_single_scan(self, client):
        import storage

        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite3"
            url = "https://example.com"
            storage.save_scan_result(_make_result(url, 70), db_path=db)

            with _patch_db(db):
                res = client.get("/api/trend", params={"url": url, "n": 5})
                assert res.status_code == 200
                data = res.json()
                assert data["delta"] is None

    def test_trend_missing_url_param(self, client):
        res = client.get("/api/trend")
        # FastAPI returns 422 when a required query param is missing
        assert res.status_code == 422


class _patch_db:
    """Context manager that patches storage.DEFAULT_DB_PATH to a temp DB."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def __enter__(self):
        import storage
        self._orig = storage.DEFAULT_DB_PATH
        storage.DEFAULT_DB_PATH = self.db_path
        return self

    def __exit__(self, *exc):
        import storage
        storage.DEFAULT_DB_PATH = self._orig

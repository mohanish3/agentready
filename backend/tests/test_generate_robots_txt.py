"""Tests for the One-Click robots.txt Fix Generator feature.

The feature adds a deterministic, offline robots.txt remediation download to the
Fix Toolkit for the AI Crawler Access check (the single highest-weighted check,
20 pts). When a scan finds that robots.txt blocks any of AI_BOTS, the user gets
a download of a corrected robots.txt that preserves every existing rule line and
appends an explicit ``User-agent: <bot>`` / ``Allow: /`` block for each blocked
bot.

These tests verify the three backend surfaces named in the brief:
  - scanner._blocked_ai_bots(robots_text)      shared blocked-bot helper
  - scanner.generate_robots_txt(result)        public generator (append-only)
  - reports.generate_robots_txt_file(result)   -> (filename, content)
  - POST /api/generate/robots-txt              FastAPI download endpoint

All cases are offline and deterministic (no network). They must PASS once the
feature is implemented and FAIL on a base that lacks it.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# ---------------------------------------------------------------------------
# Fixtures: raw robots.txt samples and a realistic scan result dict
# ---------------------------------------------------------------------------

# A robots.txt that blocks every one of the five AI bots via a wildcard rule.
BLOCKED_ALL = (
    "User-agent: *\n"
    "Disallow: /\n"
)

# A robots.txt that blocks two specific bots and leaves the rest open.
BLOCKED_TWO = (
    "User-agent: *\n"
    "Allow: /\n"
    "\n"
    "User-agent: GPTBot\n"
    "Disallow: /\n"
    "\n"
    "User-agent: CCBot\n"
    "Disallow: /*\n"
)

# A clean robots.txt that allows all five AI bots (explicit Allow blocks).
CLEAN = (
    "User-agent: GPTBot\n"
    "Allow: /\n"
    "User-agent: ClaudeBot\n"
    "Allow: /\n"
    "User-agent: PerplexityBot\n"
    "Allow: /\n"
    "User-agent: CCBot\n"
    "Allow: /\n"
    "User-agent: GoogleExtendedBot\n"
    "Allow: /\n"
)


def _make_scan_result(robots_txt):
    """Build a minimal scan result dict carrying the raw robots.txt."""
    return {
        "url": "https://acme.example.com",
        "score": 60,
        "checks": [
            {
                "check": "AI Crawler Access",
                "key": "ai_crawler_access",
                "status": "fail",
                "points_earned": 0,
                "points_max": 20,
                "points_lost": 20,
                "detail": "Per-crawler breakdown: GPTBot, CCBot blocked.",
                "action": "Edit robots.txt: add explicit Allow blocks.",
                "effort_level": "Easy",
                "effort_time": "30 min",
            },
        ],
        "recommendations": [
            {"key": "ai_crawler_access", "status": "fail", "points_lost": 20},
        ],
        "subpages": {},
        "robots_txt": robots_txt,
        "next_step": {
            "key": "ai_crawler_access",
            "points_gain": 20,
            "workflow": "Download the corrected robots.txt.",
        },
    }


def _all_ai_bots():
    import scanner
    return list(scanner.AI_BOTS)


def _expect_blocked_bots(robots_text):
    """The set of AI bots the given robots.txt blocks, per the shared helper."""
    import scanner
    assert hasattr(scanner, "_blocked_ai_bots"), (
        "scanner._blocked_ai_bots is not defined. The check and the generator "
        "must share one blocked-bot helper so they never drift."
    )
    return set(scanner._blocked_ai_bots(robots_text))


# ---------------------------------------------------------------------------
# 1. scanner._blocked_ai_bots  (shared helper)
# ---------------------------------------------------------------------------

class TestBlockedAiBotsHelper:
    """The scanner must expose a shared _blocked_ai_bots(robots_text) helper."""

    def test_function_exists(self):
        import scanner
        assert hasattr(scanner, "_blocked_ai_bots"), (
            "scanner._blocked_ai_bots(robots_text) must exist and be called from "
            "BOTH _check_ai_crawler_access and the generator."
        )
        import inspect
        assert callable(scanner._blocked_ai_bots)

    def test_returns_list(self):
        import scanner
        result = scanner._blocked_ai_bots(BLOCKED_ALL)
        assert isinstance(result, list)

    def test_wildcard_disallow_blocks_all_five(self):
        blocked = _expect_blocked_bots(BLOCKED_ALL)
        assert set(_all_ai_bots()) == blocked

    def test_specific_disallow_blocks_only_those(self):
        blocked = _expect_blocked_bots(BLOCKED_TWO)
        assert blocked == {"GPTBot", "CCBot"}

    def test_clean_allows_none(self):
        blocked = _expect_blocked_bots(CLEAN)
        assert blocked == set()


# ---------------------------------------------------------------------------
# 2. scanner.generate_robots_txt  (public, append-only generator)
# ---------------------------------------------------------------------------

class TestScannerGenerateRobotsTxt:
    """scanner.generate_robots_txt(result) reads result['robots_txt'] and appends
    an Allow block per blocked bot, preserving existing lines verbatim."""

    def test_function_exists(self):
        import scanner
        assert hasattr(scanner, "generate_robots_txt"), (
            "scanner.generate_robots_txt(result) is not defined."
        )
        assert callable(scanner.generate_robots_txt)

    def test_blocked_input_appends_allow_blocks(self):
        import scanner
        result = _make_scan_result(BLOCKED_TWO)
        content = scanner.generate_robots_txt(result)
        assert isinstance(content, str)
        assert len(content) > 0
        for bot in _expect_blocked_bots(BLOCKED_TWO):
            assert f"User-agent: {bot}" in content
            assert "Allow: /" in content

    def test_original_lines_preserved_verbatim(self):
        import scanner
        original = BLOCKED_TWO
        result = _make_scan_result(original)
        content = scanner.generate_robots_txt(result)
        # Append-only: every original line must survive unchanged.
        for line in original.splitlines():
            assert line in content.splitlines(), (
                f"original line lost/rewritten: {line!r}"
            )
        # The corrected text must be the original plus additions, not a rewrite.
        assert content.startswith(original.rstrip())

    def test_clean_input_is_noop(self):
        import scanner
        result = _make_scan_result(CLEAN)
        content = scanner.generate_robots_txt(result)
        # Nothing blocked -> no new bot Allow blocks are introduced.
        assert content is None or content == CLEAN

    def test_missing_robots_txt_returns_none(self):
        import scanner
        result = _make_scan_result(None)
        content = scanner.generate_robots_txt(result)
        assert content is None

    def test_wildcard_block_yields_five_allow_blocks(self):
        import scanner
        result = _make_scan_result(BLOCKED_ALL)
        content = scanner.generate_robots_txt(result)
        assert content is not None
        for bot in _all_ai_bots():
            assert f"User-agent: {bot}" in content


# ---------------------------------------------------------------------------
# 3. reports.generate_robots_txt_file  -> (filename, content)
# ---------------------------------------------------------------------------

class TestReportsGenerateRobotsTxtFile:
    """reports.generate_robots_txt_file(result) returns (filename, content) where
    filename == robots_<domain>.txt, mirroring the llms/JSON-LD file generators."""

    def test_function_exists(self):
        import reports
        assert hasattr(reports, "generate_robots_txt_file"), (
            "reports.generate_robots_txt_file(result) is not defined."
        )
        assert callable(reports.generate_robots_txt_file)

    def test_returns_filename_and_content_tuple(self):
        import reports
        result = _make_scan_result(BLOCKED_TWO)
        out = reports.generate_robots_txt_file(result)
        assert isinstance(out, tuple)
        assert len(out) == 2
        filename, content = out
        assert isinstance(filename, str)
        assert isinstance(content, str)

    def test_filename_is_robots_domain_txt(self):
        import reports
        result = _make_scan_result(BLOCKED_TWO)
        filename, _content = reports.generate_robots_txt_file(result)
        assert filename == "robots_acme.example.com.txt", (
            f"expected robots_acme.example.com.txt, got {filename!r}"
        )

    def test_content_matches_scanner_generator(self):
        import reports
        import scanner
        result = _make_scan_result(BLOCKED_TWO)
        _filename, content = reports.generate_robots_txt_file(result)
        assert content == scanner.generate_robots_txt(result)


# ---------------------------------------------------------------------------
# 4. POST /api/generate/robots-txt  (FastAPI endpoint)
# ---------------------------------------------------------------------------

class TestGenerateRobotsTxtEndpoint:
    """POST /api/generate/robots-txt accepts a scan result body and returns a
    text/plain attachment; 400 when the body lacks a url; graceful no-op when
    nothing is blocked."""

    @pytest.fixture()
    def client(self):
        from fastapi.testclient import TestClient
        import main
        return TestClient(main.app)

    def test_endpoint_exists(self, client):
        resp = client.post(
            "/api/generate/robots-txt",
            json=_make_scan_result(BLOCKED_TWO),
        )
        assert resp.status_code != 404, (
            "POST /api/generate/robots-txt returned 404; the endpoint is not "
            "registered in backend/main.py."
        )

    def test_blocked_body_returns_text_attachment(self, client):
        resp = client.post(
            "/api/generate/robots-txt",
            json=_make_scan_result(BLOCKED_TWO),
        )
        assert resp.status_code == 200
        assert resp.headers.get("content-type", "").startswith("text/plain")
        cd = resp.headers.get("content-disposition", "")
        assert "attachment" in cd
        assert "robots_acme.example.com.txt" in cd
        assert "Allow: /" in resp.text

    def test_missing_url_returns_400(self, client):
        body = _make_scan_result(BLOCKED_TWO)
        body.pop("url")
        resp = client.post("/api/generate/robots-txt", json=body)
        assert resp.status_code == 400

    def test_clean_body_is_graceful_noop(self, client):
        resp = client.post(
            "/api/generate/robots-txt",
            json=_make_scan_result(CLEAN),
        )
        # Nothing blocked -> must not 500. Returns 200 (empty/unchanged) or 404.
        assert resp.status_code in (200, 404)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))

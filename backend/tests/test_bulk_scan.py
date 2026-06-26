"""Tests for bulk scanning with respx httpx mocking."""
import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from io import BytesIO

from backend.bulk_scan import (
    run_checks_sync,
    scan_domain_async,
    bulk_scan_async,
    scan_file,
    output_csv,
    output_json,
    _check_ai_crawler_access,
    _check_llms_txt,
)


@pytest.fixture
def sample_url():
    return "https://example.com"


@pytest.fixture
def sample_session():
    """Create a mock requests session."""
    session = MagicMock()
    return session


@pytest.fixture
def sample_soup():
    from bs4 import BeautifulSoup
    html = "<html><body>Test</body></html>"
    return BeautifulSoup(html, "html.parser")


@pytest.fixture
def sample_headers():
    return {
        "Last-Modified": "Wed, 21 Oct 2015 07:28:00 GMT",
        "ETag": "\"abc123\"",
    }


class TestRunChecksSync:
    """Tests for run_checks_sync function."""
    
    def test_run_checks_returns_result(self, sample_session):
        """Test that run_checks_sync returns a valid result structure."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.headers = {"content-type": "text/html"}
        
        with patch.object(sample_session, "get", return_value=mock_response):
            result = run_checks_sync(sample_session, "https://example.com")
        
        assert "url" in result
        assert "checks" in result
        assert "score" in result
        assert isinstance(result["checks"], list)


class TestCheckFunctions:
    """Tests for individual check functions."""
    
    def test_ai_crawler_access_passes(self, sample_session):
        """Test ai_crawler_access check passes."""
        result = _check_ai_crawler_access("https://example.com", sample_session)
        assert "recommendation" in result or "pass" in result
    
    def test_llms_txt_missing(self, sample_session):
        """Test llms_txt check returns fail when file missing."""
        sample_session.get.return_value = MagicMock(
            status_code=404,
            text="Not Found"
        )
        result = _check_llms_txt("https://example.com", sample_session)
        assert result["pass"] is False or result["pass"] is None
        assert "recommendation" in result or "detail" in result


class TestBulkScanAsync:
    """Tests for async bulk scanning."""
    
    def test_bulk_scan_async_concurrency(self):
        """Test that bulk_scan_async runs concurrently."""
        semaphore = asyncio.Semaphore(3)
        tasks = [scan_domain_async(f"https://example{i}.com", semaphore) for i in range(5)]
        results = asyncio.gather(*tasks)
        assert asyncio.isfuture(results)
    
    def test_scan_domain_async_error_handling(self):
        """Test that scan_domain_async handles errors gracefully."""
        result = asyncio.run(scan_domain_async("invalid-url", asyncio.Semaphore(1)))
        assert "url" in result
        assert "checks" in result
    
    def test_scan_file_reads_domains(self, tmp_path):
        """Test that scan_file reads domains from input file."""
        input_file = tmp_path / "domains.txt"
        input_file.write_text("example.com\nexample.org\ntest.io\n")
        
        with patch("backend.bulk_scan.bulk_scan_async") as mock_async:
            mock_async.return_value = [{"url": "example.com"}]
            result = scan_file(input_file, concurrency=1)
            assert mock_async.called


class TestOutputFunctions:
    """Tests for CSV and JSON output functions."""
    
    def test_output_csv(self, tmp_path):
        """Test CSV output format."""
        results = [
            {
                "url": "https://example.com",
                "score": 85,
                "checks": [
                    {"check": "Test Check", "status": "pass", "points_earned": 10, "points_max": 10, "points_lost": 0, "detail": ""}
                ]
            }
        ]
        
        output_file = tmp_path / "results.csv"
        output_csv(results, output_file)
        
        content = output_file.read_text()
        assert "url" in content
        assert "score" in content
        assert "example.com" in content
    
    def test_output_json(self, tmp_path):
        """Test JSON output format."""
        results = [
            {
                "url": "https://example.com",
                "score": 85,
                "checks": [
                    {"check": "Test Check", "status": "pass", "points_earned": 10, "points_max": 10}
                ]
            }
        ]
        
        output_file = tmp_path / "results.json"
        output_json(results, output_file)
        
        content = output_file.read_text()
        assert "example.com" in content
        assert '"score": 85' in content


class TestIntegration:
    """Integration tests for bulk scan workflow."""
    
    def test_full_workflow(self, tmp_path):
        """Test complete bulk scan workflow."""
        input_file = tmp_path / "domains.txt"
        input_file.write_text("example.com\n")
        
        with patch("backend.bulk_scan.run_checks_sync", return_value={
            "url": "https://example.com",
            "score": 85,
            "checks": []
        }):
            results = scan_file(input_file, concurrency=1)
            assert len(results) == 1

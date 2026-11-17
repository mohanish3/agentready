"""Regression test: bulk_scan concurrency must work on Python 3.12+.

The original test (test_bulk_scan.py::TestBulkScanAsync::test_bulk_scan_async_concurrency)
calls asyncio.gather(*tasks) from a sync test body with NO running event loop.
On Python 3.12+, asyncio.gather resolves its loop via events.get_event_loop(),
which no longer implicitly creates a loop, so it raises:
    RuntimeError: There is no current event loop in thread 'MainThread'

This test reproduces that pattern and asserts it succeeds, so it FAILS
(by assertion) on Python 3.12+ and PASSES once the gather is run under a
real loop (asyncio.run) in the implement phase.
"""
import asyncio
from unittest.mock import patch

from backend.bulk_scan import scan_domain_async, bulk_scan_async


class TestBulkScanConcurrencyPy312:
    """Verify that gathering scan_domain_async coroutines works on Python 3.12+."""

    def test_gather_scan_tasks_sync_context(self):
        """Gathering scan tasks from a sync context must not raise RuntimeError.

        On Python < 3.12, get_event_loop() auto-created a loop, so
        asyncio.gather(*tasks) in a sync body returned a Future. On Python
        3.12+ it raises RuntimeError (no current event loop). We assert the
        gather does NOT raise; on the current (broken) code it does, so the
        assertion fails. The implement-phase fix runs the gather under
        asyncio.run() with the gather inside a coroutine.
        """
        semaphore = asyncio.Semaphore(3)
        urls = [f"https://example{i}.com" for i in range(5)]
        tasks = [scan_domain_async(url, semaphore) for url in urls]

        raised = False
        err = ""
        try:
            asyncio.gather(*tasks)
        except RuntimeError as e:
            raised = True
            err = str(e)
        finally:
            for t in tasks:
                t.close()  # close un-awaited coroutines to avoid GC warnings

        assert not raised, (
            "asyncio.gather(*tasks) called from a sync context with no running "
            f"event loop raised RuntimeError on Python 3.12+: {err}"
        )

    def test_bulk_scan_async_returns_all_results(self):
        """bulk_scan_async must return one result per domain, offline.

        Exercises the production code path (gather under a real loop via
        asyncio.run) with mocked I/O so the test is hermetic. This PASSES on
        the current code: production is correct; only the test pattern is broken.
        """
        urls = [f"https://example{i}.com" for i in range(3)]

        async def _fake_get(self, url, **kwargs):
            return type("Resp", (), {
                "status_code": 200,
                "text": "<html><body>ok</body></html>",
                "headers": {},
                "raise_for_status": lambda: None,
            })()

        async def _fake_to_thread(fn, *args, **kwargs):
            return {"url": args[1], "checks": [], "score": 85}

        with patch("httpx.AsyncClient.get", side_effect=_fake_get), \
             patch("asyncio.to_thread", side_effect=_fake_to_thread):
            results = asyncio.run(bulk_scan_async(urls, concurrency=2))

        assert len(results) == 3, f"expected 3 results, got {len(results)}"
        for i, r in enumerate(results):
            assert r["url"] == urls[i], f"result[{i}].url = {r['url']}, expected {urls[i]}"

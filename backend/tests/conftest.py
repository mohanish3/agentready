"""Test infrastructure: ensure a current event loop exists for sync-context asyncio calls.

On Python 3.12+, asyncio.get_event_loop() no longer implicitly creates a loop;
it raises RuntimeError when no loop is set and none is running. Some tests call
asyncio.gather() from a plain sync test body (no running loop). This autouse
fixture sets a loop when none exists so those calls resolve correctly, and closes
the loop it created on teardown to avoid leaking one across tests.
"""
import asyncio
import pytest


@pytest.fixture(autouse=True)
def _ensure_current_event_loop():
    """Provide a current event loop for sync-context asyncio calls (3.12+ compat)."""
    created = False
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        created = True
    yield
    if created:
        loop.close()
        asyncio.set_event_loop(None)

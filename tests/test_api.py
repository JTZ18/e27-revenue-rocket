"""Test FastAPI service."""
import pytest
from httpx import ASGITransport, AsyncClient

from intel_engine.api import app


@pytest.mark.asyncio
async def test_healthcheck():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        r = await ac.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

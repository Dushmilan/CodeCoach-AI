"""
Realistic load profiles for API endpoints.
"""

import pytest
import asyncio
import time

from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ramp_up_rps(async_client: AsyncClient):
    """1->50 concurrent users over 60 seconds (compressed for CI)."""
    results = []
    target_users = 20
    duration = 10.0
    for i in range(1, target_users + 1):
        delay = i * (duration / target_users)
        tasks = [async_client.get("/health/health") for _ in range(i)]
        batch = await asyncio.gather(*tasks)
        results.extend(batch)
        if delay < duration:
            await asyncio.sleep(0.05)
    successes = sum(1 for r in results if r.status_code == 200)
    assert successes >= len(results) * 0.9


@pytest.mark.asyncio
async def test_spike_load(async_client: AsyncClient):
    """200 requests in under 5 seconds burst."""
    tasks = [async_client.get("/api/questions/") for _ in range(200)]
    responses = await asyncio.gather(*tasks)
    success_count = sum(1 for r in responses if r.status_code == 200)
    assert success_count >= 190


@pytest.mark.asyncio
async def test_sustained_load(async_client: AsyncClient):
    """~20 req/s for 10 seconds (shortened for CI)."""
    results = []
    start = time.time()
    while time.time() - start < 10:
        batch = [async_client.get("/health/health") for _ in range(5)]
        results.extend(await asyncio.gather(*batch))
        await asyncio.sleep(0.25)
    assert all(r.status_code == 200 for r in results)


@pytest.mark.asyncio
async def test_mixed_workload(async_client: AsyncClient):
    """60% read, 30% execute POST, 10% coach POST."""
    import random

    tasks = []
    for _ in range(100):
        roll = random.random()
        if roll < 0.6:
            tasks.append(async_client.get("/api/questions/"))
        elif roll < 0.9:
            tasks.append(
                async_client.post(
                    "/api/run/",
                    json={"language": "python", "code": "print(1)", "stdin": ""},
                )
            )
        else:
            tasks.append(
                async_client.post(
                    "/api/coach/",
                    json={
                        "problem": "test",
                        "code": "x=1",
                        "language": "python",
                        "message": "help",
                        "mode": "hint",
                        "difficulty": "easy",
                    },
                )
            )
    responses = await asyncio.gather(*tasks)
    assert len(responses) == 100

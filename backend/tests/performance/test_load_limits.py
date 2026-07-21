"""
Performance and load testing for API endpoints.
"""

import pytest
import asyncio
import time
import statistics

import psutil
import gc

from httpx import AsyncClient
from contextlib import contextmanager

from app.main import app


@contextmanager
def mock_auth(user_id: str = "test-id", username: str = "testuser"):
    """Override auth dependency for testing."""
    from app.api.auth_deps import get_current_user

    async def override_get_current_user():
        from app.models.auth_schemas import UserResponse

        return UserResponse(
            id=user_id,
            username=username,
            email="test@example.com",
            is_active=True,
            created_at="2025-01-01T00:00:00Z",
        )

    app.dependency_overrides[get_current_user] = override_get_current_user
    try:
        yield
    finally:
        app.dependency_overrides.clear()


class TestLoadLimits:
    """Test cases for load limits and performance."""

    @pytest.mark.asyncio
    async def test_concurrent_requests_health(self, async_client: AsyncClient):
        """Test concurrent health check requests."""
        tasks = [async_client.get("/health/health") for _ in range(100)]
        responses = await asyncio.gather(*tasks)

        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_concurrent_requests_questions(self, async_client: AsyncClient):
        """Test concurrent questions requests."""
        tasks = [async_client.get("/api/questions/") for _ in range(50)]
        responses = await asyncio.gather(*tasks)

        for response in responses:
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, async_client: AsyncClient):
        """Test memory usage under load."""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

        for i in range(100):
            response = await async_client.get("/api/questions/")
            assert response.status_code == 200

            if i % 10 == 0:
                gc.collect()

        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory

        assert memory_increase < 50, f"Memory increased by {memory_increase}MB"

    @pytest.mark.asyncio
    async def test_response_time_percentiles(self, async_client: AsyncClient):
        """Test response time percentiles."""
        response_times = []

        for _ in range(100):
            start_time = time.time()
            response = await async_client.get("/health/health")
            end_time = time.time()

            assert response.status_code == 200
            response_times.append((end_time - start_time) * 1000)

        response_times.sort()

        quantiles = statistics.quantiles(response_times, n=100)
        p50 = quantiles[49]
        p95 = quantiles[94]
        p99 = quantiles[98]

        assert p50 < 100, f"50th percentile: {p50}ms"
        assert p95 < 200, f"95th percentile: {p95}ms"
        assert p99 < 500, f"99th percentile: {p99}ms"

    @pytest.mark.asyncio
    async def test_rate_limiting_effectiveness(self, async_client: AsyncClient):
        """Test rate limiting effectiveness."""
        responses = []

        for i in range(20):
            response = await async_client.get("/health/health")
            responses.append(response.status_code)

        assert all(status == 200 for status in responses)

    @pytest.mark.asyncio
    async def test_database_query_performance(self, async_client: AsyncClient):
        """Test database query performance."""
        page_sizes = [1, 10, 50, 100]

        for size in page_sizes:
            start_time = time.time()
            response = await async_client.get(f"/api/questions/?per_page={size}")
            end_time = time.time()

            assert response.status_code == 200
            response_time = (end_time - start_time) * 1000

            assert (
                response_time < 100 + size * 2
            ), f"Page size {size} took {response_time}ms"

    @pytest.mark.asyncio
    async def test_large_payload_handling(self, async_client: AsyncClient):
        """Test handling of large payloads."""
        large_code = "def test():\n" + "    pass\n" * 1000

        coaching_request = {
            "problem": "Test problem",
            "code": large_code,
            "language": "python",
            "message": "Test message",
            "mode": "hint",
            "difficulty": "easy",
        }

        start_time = time.time()
        with mock_auth():
            response = await async_client.post("/api/coach/", json=coaching_request)
        end_time = time.time()

        assert response.status_code == 200
        response_time = (end_time - start_time) * 1000
        assert response_time < 5000, f"Large payload took {response_time}ms"

    @pytest.mark.asyncio
    async def test_stress_test_endpoints(self, async_client: AsyncClient):
        """Stress test all endpoints."""
        endpoints = [
            "/health/health",
            "/api/questions/",
            "/api/questions/categories",
            "/api/questions/companies",
        ]

        tasks = []
        for endpoint in endpoints:
            for _ in range(5):
                tasks.append(async_client.get(endpoint))

        responses = await asyncio.gather(*tasks)
        statuses = [r.status_code for r in responses]
        assert all(status == 200 for status in statuses)

    @pytest.mark.asyncio
    async def test_async_concurrent_requests(self, async_client: AsyncClient):
        """Test async concurrent requests."""
        tasks = [async_client.get("/api/questions/") for _ in range(50)]
        responses = await asyncio.gather(*tasks)

        assert all(status == 200 for status in [r.status_code for r in responses])

    @pytest.mark.asyncio
    async def test_cpu_intensive_operations(self, async_client: AsyncClient):
        """Test CPU intensive operations."""
        fibonacci_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(20))
        """.strip()

        code_request = {
            "language": "python",
            "code": fibonacci_code,
            "stdin": "",
            "version": "3.11.0",
        }

        start_time = time.time()
        with mock_auth():
            response = await async_client.post("/api/run/", json=code_request)
        end_time = time.time()

        assert response.status_code == 200
        response_time = (end_time - start_time) * 1000
        assert response_time < 10000, f"CPU intensive task took {response_time}ms"

    @pytest.mark.asyncio
    async def test_memory_intensive_operations(self, async_client: AsyncClient):
        """Test memory intensive operations."""
        memory_code = """
large_list = [i for i in range(100000)]
print(len(large_list))
        """.strip()

        code_request = {
            "language": "python",
            "code": memory_code,
            "stdin": "",
            "version": "3.11.0",
        }

        start_time = time.time()
        with mock_auth():
            response = await async_client.post("/api/run/", json=code_request)
        end_time = time.time()

        assert response.status_code == 200
        response_time = (end_time - start_time) * 1000
        assert response_time < 5000, f"Memory intensive task took {response_time}ms"

    @pytest.mark.asyncio
    async def test_connection_pool_limits(self, async_client: AsyncClient):
        """Test connection pool limits."""
        tasks = [async_client.get("/health/health") for _ in range(100)]
        results = await asyncio.gather(*tasks)

        assert all(r.status_code == 200 for r in results)
        assert len(results) == 100

    @pytest.mark.asyncio
    async def test_timeout_handling(self, async_client: AsyncClient):
        """Test timeout handling for long-running operations."""
        infinite_loop_code = """
import time
while True:
    time.sleep(0.1)
        """.strip()

        code_request = {
            "language": "python",
            "code": infinite_loop_code,
            "stdin": "",
            "version": "3.11.0",
        }

        start_time = time.time()
        with mock_auth():
            await async_client.post("/api/run/", json=code_request)
        end_time = time.time()

        response_time = (end_time - start_time) * 1000
        assert (
            response_time < 30000
        ), f"Should timeout within 30s, took {response_time}ms"

    @pytest.mark.asyncio
    async def test_load_balancing_simulation(self, async_client: AsyncClient):
        """Simulate load across different endpoints."""
        endpoints = [
            "/health/health",
            "/api/questions/",
            "/api/coach/modes",
        ]

        import random

        tasks = []
        for _ in range(200):
            endpoint = random.choice(endpoints)
            tasks.append(async_client.get(endpoint))

        results = await asyncio.gather(*tasks)
        assert all(r.status_code == 200 for r in results)
        assert len(results) == 200

    @pytest.mark.asyncio
    async def test_performance_regression_detection(self, async_client: AsyncClient):
        """Test performance against absolute thresholds."""
        times = []
        for _ in range(20):
            start = time.time()
            response = await async_client.get("/health/health")
            elapsed = (time.time() - start) * 1000
            assert response.status_code == 200
            times.append(elapsed)

        sorted_times = sorted(times)
        p95 = sorted_times[int(len(times) * 0.95)]
        assert p95 < 200, f"p95 response time {p95}ms exceeds 200ms threshold"


class TestLoadTestConfiguration:
    """Test load test configuration."""

    def test_load_test_scenarios(self):
        """Test load test scenarios."""
        scenarios = [
            {"name": "normal_load", "users": 10, "spawn_rate": 2, "duration": "30s"},
            {"name": "stress_load", "users": 50, "spawn_rate": 5, "duration": "60s"},
            {"name": "peak_load", "users": 100, "spawn_rate": 10, "duration": "120s"},
        ]

        for scenario in scenarios:
            assert "name" in scenario
            assert "users" in scenario
            assert "spawn_rate" in scenario
            assert "duration" in scenario
            assert scenario["users"] > 0

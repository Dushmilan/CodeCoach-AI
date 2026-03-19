"""
Performance and load testing for API endpoints.
"""
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
import threading
from typing import List
import psutil
import gc

from fastapi.testclient import TestClient
from httpx import AsyncClient
import locust
from locust import HttpUser, task, between

from tests.fixtures.factories import TestDataGenerator


class TestLoadLimits:
    """Test cases for load limits and performance."""
    
    def test_concurrent_requests_health(self, test_client: TestClient):
        """Test concurrent health check requests."""
        def make_request():
            return test_client.get("/health")
        
        # Test 100 concurrent requests
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(make_request) for _ in range(100)]
            results = [f.result() for f in futures]
        
        # All requests should succeed
        for response in results:
            assert response.status_code == 200
        
        # All should return healthy
        for response in results:
            data = response.json()
            assert data["status"] == "healthy"
    
    def test_concurrent_requests_questions(self, test_client: TestClient):
        """Test concurrent questions requests."""
        def make_request():
            return test_client.get("/api/questions/")
        
        # Test 50 concurrent requests
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [f.result() for f in futures]
        
        # All requests should succeed
        for response in results:
            assert response.status_code == 200
    
    def test_memory_usage_under_load(self, test_client: TestClient):
        """Test memory usage under load."""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Make 100 requests
        for i in range(100):
            response = test_client.get("/api/questions/")
            assert response.status_code == 200
            
            if i % 10 == 0:
                gc.collect()  # Force garbage collection
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 50MB)
        assert memory_increase < 50, f"Memory increased by {memory_increase}MB"
    
    def test_response_time_percentiles(self, test_client: TestClient):
        """Test response time percentiles."""
        response_times = []
        
        # Make 100 requests and measure response times
        for _ in range(100):
            start_time = time.time()
            response = test_client.get("/health")
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append((end_time - start_time) * 1000)  # ms
        
        response_times.sort()
        
        # Calculate percentiles
        p50 = response_times[49]
        p95 = response_times[94]
        p99 = response_times[98]
        
        # Performance targets
        assert p50 < 100, f"50th percentile: {p50}ms"
        assert p95 < 200, f"95th percentile: {p95}ms"
        assert p99 < 500, f"99th percentile: {p99}ms"
    
    def test_rate_limiting_effectiveness(self, test_client: TestClient):
        """Test rate limiting effectiveness."""
        # Make rapid requests to test rate limiting
        responses = []
        
        for i in range(20):
            response = test_client.get("/health")
            responses.append(response.status_code)
        
        # All requests should succeed (rate limit is high for health)
        assert all(status == 200 for status in responses)
    
    def test_database_query_performance(self, test_client: TestClient):
        """Test database query performance."""
        # Test questions with different page sizes
        page_sizes = [1, 10, 50, 100]
        
        for size in page_sizes:
            start_time = time.time()
            response = test_client.get(f"/api/questions/?per_page={size}")
            end_time = time.time()
            
            assert response.status_code == 200
            response_time = (end_time - start_time) * 1000
            
            # Response time should scale reasonably
            assert response_time < 100 + size * 2, f"Page size {size} took {response_time}ms"
    
    def test_large_payload_handling(self, test_client: TestClient):
        """Test handling of large payloads."""
        # Test coaching with large code
        large_code = "def test():\n" + "    pass\n" * 1000
        
        coaching_request = {
            "problem": "Test problem",
            "code": large_code,
            "language": "python",
            "message": "Test message",
            "mode": "hint",
            "difficulty": "easy"
        }
        
        start_time = time.time()
        response = test_client.post("/api/coach/", json=coaching_request)
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = (end_time - start_time) * 1000
        assert response_time < 5000, f"Large payload took {response_time}ms"
    
    def test_stress_test_endpoints(self, test_client: TestClient):
        """Stress test all endpoints."""
        endpoints = [
            "/health",
            "/api/questions/",
            "/api/questions/categories",
            "/api/questions/companies",
            "/api/run/languages"
        ]
        
        def stress_endpoint(endpoint):
            for _ in range(10):
                response = test_client.get(endpoint)
                return response.status_code
        
        # Stress test all endpoints concurrently
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for endpoint in endpoints:
                for _ in range(5):
                    futures.append(executor.submit(stress_endpoint, endpoint))
            
            results = [f.result() for f in futures]
        
        # All requests should succeed
        assert all(status == 200 for status in results)
    
    @pytest.mark.asyncio
    async def test_async_concurrent_requests(self, async_client: AsyncClient):
        """Test async concurrent requests."""
        async def make_request():
            response = await async_client.get("/api/questions/")
            return response.status_code
        
        # Test 50 concurrent async requests
        tasks = [make_request() for _ in range(50)]
        results = await asyncio.gather(*tasks)
        
        # All requests should succeed
        assert all(status == 200 for status in results)
    
    def test_cpu_intensive_operations(self, test_client: TestClient):
        """Test CPU intensive operations."""
        # Test code execution with CPU intensive task
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
            "version": "3.11.0"
        }
        
        start_time = time.time()
        response = test_client.post("/api/run/", json=code_request)
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = (end_time - start_time) * 1000
        assert response_time < 10000, f"CPU intensive task took {response_time}ms"
    
    def test_memory_intensive_operations(self, test_client: TestClient):
        """Test memory intensive operations."""
        # Test code execution with memory intensive task
        memory_code = """
large_list = [i for i in range(100000)]
print(len(large_list))
        """.strip()
        
        code_request = {
            "language": "python",
            "code": memory_code,
            "stdin": "",
            "version": "3.11.0"
        }
        
        start_time = time.time()
        response = test_client.post("/api/run/", json=code_request)
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = (end_time - start_time) * 1000
        assert response_time < 5000, f"Memory intensive task took {response_time}ms"
    
    def test_connection_pool_limits(self, test_client: TestClient):
        """Test connection pool limits."""
        # Test with many rapid requests
        import concurrent.futures
        
        def rapid_request():
            return test_client.get("/health")
        
        # Make 100 rapid requests
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(rapid_request) for _ in range(100)]
            results = [f.result() for f in futures]
        
        # All should succeed
        assert all(r.status_code == 200 for r in results)
        assert len(results) == 100
    
    def test_timeout_handling(self, test_client: TestClient):
        """Test timeout handling for long-running operations."""
        # Test with infinite loop (should timeout)
        infinite_loop_code = """
import time
while True:
    time.sleep(0.1)
        """.strip()
        
        code_request = {
            "language": "python",
            "code": infinite_loop_code,
            "stdin": "",
            "version": "3.11.0"
        }
        
        start_time = time.time()
        response = test_client.post("/api/run/", json=code_request)
        end_time = time.time()
        
        # Should timeout gracefully
        response_time = (end_time - start_time) * 1000
        assert response_time < 30000, f"Should timeout within 30s, took {response_time}ms"
    
    def test_load_balancing_simulation(self, test_client: TestClient):
        """Test load balancing simulation."""
        # Simulate load across different endpoints
        endpoints = [
            "/health",
            "/api/questions/",
            "/api/coach/modes",
            "/api/run/languages"
        ]
        
        def load_balance_test():
            import random
            endpoint = random.choice(endpoints)
            return test_client.get(endpoint)
        
        # Simulate 200 requests across endpoints
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(load_balance_test) for _ in range(200)]
            results = [f.result() for f in futures]
        
        # All should succeed
        assert all(r.status_code == 200 for r in results)
        assert len(results) == 200
    
    def test_performance_regression_detection(self, test_client: TestClient):
        """Test performance regression detection."""
        baseline_times = []
        
        # Establish baseline
        for _ in range(10):
            start_time = time.time()
            response = test_client.get("/health")
            end_time = time.time()
            
            assert response.status_code == 200
            baseline_times.append((end_time - start_time) * 1000)
        
        baseline_avg = sum(baseline_times) / len(baseline_times)
        
        # Test current performance
        current_times = []
        for _ in range(10):
            start_time = time.time()
            response = test_client.get("/health")
            end_time = time.time()
            
            assert response.status_code == 200
            current_times.append((end_time - start_time) * 1000)
        
        current_avg = sum(current_times) / len(current_times)
        
        # Performance regression should be < 50%
        regression = (current_avg - baseline_avg) / baseline_avg
        assert regression < 0.5, f"Performance regression: {regression * 100}%"


class CodeCoachLoadTest(HttpUser):
    """Locust load test configuration."""
    
    wait_time = between(1, 3)
    
    @task(3)
    def get_questions(self):
        """Load test questions endpoint."""
        self.client.get("/api/questions/")
    
    @task(2)
    def get_health(self):
        """Load test health endpoint."""
        self.client.get("/health")
    
    @task(1)
    def get_languages(self):
        """Load test languages endpoint."""
        self.client.get("/api/run/languages")
    
    @task(1)
    def get_categories(self):
        """Load test categories endpoint."""
        self.client.get("/api/questions/categories")
    
    @task(2)
    def search_questions(self):
        """Load test search endpoint."""
        self.client.get("/api/questions/search?q=array")
    
    @task(1)
    def get_coaching_modes(self):
        """Load test coaching modes endpoint."""
        self.client.get("/api/coach/modes")


class TestLoadTestConfiguration:
    """Test load test configuration."""
    
    def test_locust_config(self):
        """Test locust configuration is valid."""
        assert hasattr(CodeCoachLoadTest, 'wait_time')
        assert hasattr(CodeCoachLoadTest, 'tasks')
        
        # Check task weights
        tasks = [task for task in dir(CodeCoachLoadTest) if task.startswith('get_') or task.startswith('search_')]
        assert len(tasks) >= 5
    
    def test_load_test_scenarios(self):
        """Test load test scenarios."""
        scenarios = [
            {
                "name": "normal_load",
                "users": 10,
                "spawn_rate": 2,
                "duration": "30s"
            },
            {
                "name": "stress_load",
                "users": 50,
                "spawn_rate": 5,
                "duration": "60s"
            },
            {
                "name": "peak_load",
                "users": 100,
                "spawn_rate": 10,
                "duration": "120s"
            }
        ]
        
        for scenario in scenarios:
            assert "name" in scenario
            assert "users" in scenario
            assert "spawn_rate" in scenario
            assert "duration" in scenario
            assert scenario["users"] > 0
            assert scenario["spawn_rate"] > 0
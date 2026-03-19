"""
Integration tests for health check endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


class TestHealthEndpoints:
    """Test cases for health check endpoints."""
    
    def test_health_check_basic(self, test_client: TestClient):
        """Test basic health check endpoint."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "codecoach-ai-backend"
        assert "timestamp" in data
        assert "dependencies" in data
        assert data["dependencies"]["fastapi"] == "running"
        assert data["dependencies"]["uvicorn"] == "running"
    
    def test_health_check_detailed(self, test_client: TestClient):
        """Test detailed health check endpoint."""
        response = test_client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "codecoach-ai-backend"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data
        assert "system" in data
        assert "features" in data
        assert "dependencies" in data
        
        # Check system information
        system = data["system"]
        assert "python_version" in system
        assert "fastapi_version" in system
        assert "uvicorn_version" in system
        
        # Check features
        features = data["features"]
        assert features["ai_coaching"] == "enabled"
        assert features["code_execution"] == "enabled"
        assert features["questions_api"] == "enabled"
        assert features["rate_limiting"] == "enabled"
        
        # Check dependencies
        dependencies = data["dependencies"]
        assert "nvidia_nim" in dependencies
        assert "piston_api" in dependencies
        assert "questions_db" in dependencies
    
    @pytest.mark.asyncio
    async def test_health_check_async(self, async_client: AsyncClient):
        """Test health check with async client."""
        response = await async_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "codecoach-ai-backend"
    
    def test_health_check_response_format(self, test_client: TestClient):
        """Test health check response format consistency."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        
        # Validate response schema
        required_fields = ["status", "service", "timestamp", "dependencies"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Validate timestamp format (ISO 8601)
        timestamp = data["timestamp"]
        assert timestamp.endswith("Z") or "+" in timestamp, "Timestamp should be in ISO 8601 format"
    
    def test_health_check_error_handling(self, test_client: TestClient):
        """Test health check error handling."""
        # Test with invalid HTTP method
        response = test_client.post("/health")
        assert response.status_code == 405
        
        response = test_client.put("/health")
        assert response.status_code == 405
        
        response = test_client.delete("/health")
        assert response.status_code == 405
    
    def test_health_check_caching_headers(self, test_client: TestClient):
        """Test health check caching headers."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        
        # Check for appropriate caching headers
        cache_control = response.headers.get("cache-control", "")
        # Health checks should not be cached
        assert "no-cache" in cache_control.lower() or "no-store" in cache_control.lower()
    
    def test_health_check_response_time(self, test_client: TestClient):
        """Test health check response time is within acceptable limits."""
        import time
        
        start_time = time.time()
        response = test_client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Response should be very fast (< 100ms)
        response_time = (end_time - start_time) * 1000
        assert response_time < 100, f"Health check took {response_time}ms, expected < 100ms"
    
    def test_health_check_detailed_response_time(self, test_client: TestClient):
        """Test detailed health check response time."""
        import time
        
        start_time = time.time()
        response = test_client.get("/health/detailed")
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Detailed check should still be fast (< 200ms)
        response_time = (end_time - start_time) * 1000
        assert response_time < 200, f"Detailed health check took {response_time}ms, expected < 200ms"
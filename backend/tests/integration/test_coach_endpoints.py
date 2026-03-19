"""
Integration tests for coach endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import json
from unittest.mock import patch

from app.models.schemas import CoachingMode, Language, Difficulty


@pytest.mark.usefixtures("test_env_vars")
class TestCoachEndpoints:
    """Test cases for coach endpoints."""
    
    def test_get_coaching_basic(self, test_client: TestClient, test_env_vars):
        """Test basic coaching endpoint."""
        coaching_request = {
            "problem": "Find the maximum element in an array",
            "code": "def max_element(arr):\n    return max(arr)",
            "language": "python",
            "message": "Is this the most efficient solution?",
            "mode": "review",
            "difficulty": "easy"
        }

        response = test_client.post("/api/coach/", json=coaching_request)

        assert response.status_code == 200
        data = response.json()

        assert "response" in data
        assert data["mode"] == "review"
        assert data["language"] == "python"
        assert len(data["response"]) > 0
    
    def test_get_coaching_streaming(self, test_client: TestClient):
        """Test streaming coaching endpoint."""
        coaching_request = {
            "problem": "Find the maximum element in an array",
            "code": "def max_element(arr):\n    return max(arr)",
            "language": "python",
            "message": "Is this the most efficient solution?",
            "mode": "review",
            "difficulty": "easy"
        }
        
        response = test_client.post("/api/coach/stream", json=coaching_request)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Check for SSE format
        content = response.text
        assert "data:" in content
        assert "done" in content
    
    def test_get_coaching_modes(self, test_client: TestClient):
        """Test getting available coaching modes."""
        response = test_client.get("/api/coach/modes")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "modes" in data
        assert "descriptions" in data
        
        expected_modes = ["hint", "review", "explain", "debug"]
        assert set(data["modes"]) == set(expected_modes)
        
        # Check descriptions
        descriptions = data["descriptions"]
        assert "hint" in descriptions
        assert "review" in descriptions
        assert "explain" in descriptions
        assert "debug" in descriptions
    
    def test_get_supported_languages(self, test_client: TestClient):
        """Test getting supported programming languages."""
        response = test_client.get("/api/coach/languages")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "languages" in data
        assert "descriptions" in data
        
        expected_languages = ["python", "javascript", "java", "cpp", "c", "go", "rust", "typescript"]
        assert set(data["languages"]) >= set(expected_languages)
    
    def test_coaching_invalid_language(self, test_client: TestClient):
        """Test coaching with invalid language."""
        coaching_request = {
            "problem": "Test problem",
            "code": "test code",
            "language": "invalid_language",
            "message": "test message",
            "mode": "hint",
            "difficulty": "easy"
        }
        
        response = test_client.post("/api/coach/", json=coaching_request)
        
        assert response.status_code == 422  # Validation error
    
    def test_coaching_invalid_mode(self, test_client: TestClient):
        """Test coaching with invalid mode."""
        coaching_request = {
            "problem": "Test problem",
            "code": "test code",
            "language": "python",
            "message": "test message",
            "mode": "invalid_mode",
            "difficulty": "easy"
        }
        
        response = test_client.post("/api/coach/", json=coaching_request)
        
        assert response.status_code == 422  # Validation error
    
    def test_coaching_missing_required_fields(self, test_client: TestClient):
        """Test coaching with missing required fields."""
        # Missing problem
        coaching_request = {
            "code": "test code",
            "language": "python",
            "message": "test message",
            "mode": "hint",
            "difficulty": "easy"
        }
        
        response = test_client.post("/api/coach/", json=coaching_request)
        assert response.status_code == 422
        
        # Missing code
        coaching_request = {
            "problem": "Test problem",
            "language": "python",
            "message": "test message",
            "mode": "hint",
            "difficulty": "easy"
        }
        
        response = test_client.post("/api/coach/", json=coaching_request)
        assert response.status_code == 422
    
    def test_coaching_all_modes(self, test_client: TestClient):
        """Test coaching with all available modes."""
        base_request = {
            "problem": "Find the maximum element in an array",
            "code": "def max_element(arr):\n    return max(arr)",
            "language": "python",
            "message": "Please provide guidance",
            "difficulty": "easy"
        }
        
        modes = ["hint", "review", "explain", "debug"]
        
        for mode in modes:
            request = {**base_request, "mode": mode}
            response = test_client.post("/api/coach/", json=request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["mode"] == mode
            assert len(data["response"]) > 0
    
    def test_coaching_all_languages(self, test_client: TestClient):
        """Test coaching with all supported languages."""
        base_request = {
            "problem": "Find the maximum element in an array",
            "message": "Please provide guidance",
            "mode": "hint",
            "difficulty": "easy"
        }
        
        languages = ["python", "javascript", "java", "cpp", "c", "go", "rust", "typescript"]
        
        for language in languages:
            code_templates = {
                "python": "def solution(arr):\n    return max(arr)",
                "javascript": "function solution(arr) {\n    return Math.max(...arr);\n}",
                "java": "public int solution(int[] arr) {\n    return Arrays.stream(arr).max().getAsInt();\n}",
                "cpp": "int solution(vector<int>& arr) {\n    return *max_element(arr.begin(), arr.end());\n}",
                "c": "int solution(int* arr, int size) {\n    int max = arr[0];\n    for(int i = 1; i < size; i++) {\n        if(arr[i] > max) max = arr[i];\n    }\n    return max;\n}",
                "go": "func solution(arr []int) int {\n    max := arr[0]\n    for _, v := range arr {\n        if v > max {\n            max = v\n        }\n    }\n    return max\n}",
                "rust": "fn solution(arr: &[i32]) -> i32 {\n    *arr.iter().max().unwrap()\n}",
                "typescript": "function solution(arr: number[]): number {\n    return Math.max(...arr);\n}"
            }
            
            request = {
                **base_request,
                "language": language,
                "code": code_templates.get(language, "// Default code")
            }
            
            response = test_client.post("/api/coach/", json=request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["language"] == language
            assert len(data["response"]) > 0
    
    def test_coaching_boundary_conditions(self, test_client: TestClient):
        """Test coaching with boundary conditions."""
        # Very long problem description
        long_problem = "x" * 1000
        coaching_request = {
            "problem": long_problem,
            "code": "def test(): pass",
            "language": "python",
            "message": "short",
            "mode": "hint",
            "difficulty": "easy"
        }
        
        response = test_client.post("/api/coach/", json=coaching_request)
        assert response.status_code == 200
        
        # Very long code
        long_code = "x" * 2000
        coaching_request = {
            "problem": "Test problem",
            "code": long_code,
            "language": "python",
            "message": "short",
            "mode": "hint",
            "difficulty": "easy"
        }
        
        response = test_client.post("/api/coach/", json=coaching_request)
        assert response.status_code == 200
    
    def test_coaching_empty_strings(self, test_client: TestClient):
        """Test coaching with empty strings."""
        coaching_request = {
            "problem": "",
            "code": "",
            "language": "python",
            "message": "",
            "mode": "hint",
            "difficulty": "easy"
        }
        
        response = test_client.post("/api/coach/", json=coaching_request)
        assert response.status_code == 200  # Should handle gracefully
    
    @pytest.mark.asyncio
    async def test_coaching_async(self, async_client):
        """Test coaching with async client."""
        coaching_request = {
            "problem": "Find the maximum element in an array",
            "code": "def max_element(arr):\n    return max(arr)",
            "language": "python",
            "message": "Is this the most efficient solution?",
            "mode": "review",
            "difficulty": "easy"
        }
        
        response = await async_client.post("/api/coach/", json=coaching_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["mode"] == "review"
    
    def test_coaching_response_format(self, test_client: TestClient):
        """Test coaching response format consistency."""
        coaching_request = {
            "problem": "Test problem",
            "code": "def test(): pass",
            "language": "python",
            "message": "Test message",
            "mode": "hint",
            "difficulty": "easy"
        }
        
        response = test_client.post("/api/coach/", json=coaching_request)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        required_fields = ["response", "mode", "language"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
    
    def test_coaching_error_handling(self, test_client: TestClient):
        """Test coaching error handling."""
        # Test invalid JSON
        response = test_client.post("/api/coach/", data="invalid json")
        assert response.status_code == 422
        
        # Test with wrong HTTP method
        response = test_client.get("/api/coach/")
        assert response.status_code == 405
        
        response = test_client.put("/api/coach/")
        assert response.status_code == 405
        
        response = test_client.delete("/api/coach/")
        assert response.status_code == 405
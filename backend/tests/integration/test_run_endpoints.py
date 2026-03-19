"""
Integration tests for code execution endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


class TestRunEndpoints:
    """Test cases for code execution endpoints."""
    
    def test_execute_code_python(self, test_client: TestClient):
        """Test executing Python code."""
        code_request = {
            "language": "python",
            "code": "print('Hello, World!')\nprint(2 + 2)",
            "stdin": "",
            "version": "3.11.0"
        }
        
        response = test_client.post("/api/run/", json=code_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "stdout" in data
        assert "stderr" in data
        assert "exit_code" in data
        assert "execution_time" in data
        assert "memory_usage" in data
        assert "language" in data
        assert "version" in data
        
        assert data["language"] == "python"
        assert data["exit_code"] == 0
        assert "Hello, World!" in data["stdout"]
        assert "4" in data["stdout"]
    
    def test_execute_code_javascript(self, test_client: TestClient):
        """Test executing JavaScript code."""
        code_request = {
            "language": "javascript",
            "code": "console.log('Hello, World!');\nconsole.log(2 + 2);",
            "stdin": "",
            "version": "18.17.0"
        }
        
        response = test_client.post("/api/run/", json=code_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["language"] == "javascript"
        assert data["exit_code"] == 0
        assert "Hello, World!" in data["stdout"]
        assert "4" in data["stdout"]
    
    def test_execute_code_with_input(self, test_client: TestClient):
        """Test executing code with stdin input."""
        code_request = {
            "language": "python",
            "code": "user_input = input()\nprint(f'Hello, {user_input}!')",
            "stdin": "Alice",
            "version": "3.11.0"
        }
        
        response = test_client.post("/api/run/", json=code_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["exit_code"] == 0
        assert "Hello, Alice!" in data["stdout"]
    
    def test_execute_code_with_error(self, test_client: TestClient):
        """Test executing code that produces an error."""
        code_request = {
            "language": "python",
            "code": "print(undefined_variable)",
            "stdin": "",
            "version": "3.11.0"
        }
        
        response = test_client.post("/api/run/", json=code_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["exit_code"] != 0
        assert "NameError" in data["stderr"] or "undefined" in data["stderr"]
    
    def test_validate_code_python(self, test_client: TestClient):
        """Test validating Python code."""
        code_request = {
            "language": "python",
            "code": "def hello():\n    return 'Hello, World!'",
            "version": "3.11.0"
        }
        
        response = test_client.post("/api/run/validate", json=code_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "valid" in data
        assert "warnings" in data
        assert "errors" in data
        assert "language" in data
        
        assert data["valid"] is True
        assert data["language"] == "python"
    
    def test_validate_code_with_syntax_error(self, test_client: TestClient):
        """Test validating code with syntax errors."""
        code_request = {
            "language": "python",
            "code": "def hello(\n    return 'Hello, World!'",
            "version": "3.11.0"
        }
        
        response = test_client.post("/api/run/validate", json=code_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["valid"] is False
        assert len(data["errors"]) > 0
    
    def test_get_supported_languages(self, test_client: TestClient):
        """Test getting supported programming languages."""
        response = test_client.get("/api/run/languages")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "languages" in data
        assert "total" in data
        assert isinstance(data["languages"], list)
        assert len(data["languages"]) > 0
        
        # Check for expected languages
        expected_languages = ["python", "javascript", "java", "cpp", "c", "go", "rust"]
        actual_languages = [lang["language"] for lang in data["languages"]]
        
        for lang in expected_languages:
            assert lang in actual_languages, f"Missing expected language: {lang}"
    
    def test_get_runtimes(self, test_client: TestClient):
        """Test getting all available runtimes."""
        response = test_client.get("/api/run/runtimes")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "runtimes" in data
        assert isinstance(data["runtimes"], list)
        assert len(data["runtimes"]) > 0
    
    def test_execute_code_invalid_language(self, test_client: TestClient):
        """Test executing code with invalid language."""
        code_request = {
            "language": "invalid_language",
            "code": "print('Hello')",
            "stdin": "",
            "version": "1.0.0"
        }
        
        response = test_client.post("/api/run/", json=code_request)
        
        assert response.status_code == 200  # Should handle gracefully
        data = response.json()
        
        # Should return error in response
        assert data["exit_code"] != 0
        assert "not supported" in data["stderr"].lower()
    
    def test_execute_code_empty(self, test_client: TestClient):
        """Test executing empty code."""
        code_request = {
            "language": "python",
            "code": "",
            "stdin": "",
            "version": "3.11.0"
        }
        
        response = test_client.post("/api/run/", json=code_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["exit_code"] == 0
        assert data["stdout"] == ""
    
    def test_execute_code_complex(self, test_client: TestClient):
        """Test executing complex code."""
        code_request = {
            "language": "python",
            "code": """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")
            """.strip(),
            "stdin": "",
            "version": "3.11.0"
        }
        
        response = test_client.post("/api/run/", json=code_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["exit_code"] == 0
        assert "F(0) = 0" in data["stdout"]
        assert "F(9) = 34" in data["stdout"]
    
    def test_execute_code_memory_limit(self, test_client: TestClient):
        """Test executing code that might hit memory limits."""
        code_request = {
            "language": "python",
            "code": "large_list = [i for i in range(100000)]\nprint(len(large_list))",
            "stdin": "",
            "version": "3.11.0"
        }
        
        response = test_client.post("/api/run/", json=code_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should execute successfully or handle gracefully
        assert data["exit_code"] == 0 or "memory" in data["stderr"].lower()
    
    def test_execute_code_timeout(self, test_client: TestClient):
        """Test executing code that might timeout."""
        code_request = {
            "language": "python",
            "code": "import time\ntime.sleep(1)\nprint('Done')",
            "stdin": "",
            "version": "3.11.0"
        }
        
        response = test_client.post("/api/run/", json=code_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should execute successfully or timeout gracefully
        assert data["exit_code"] == 0 or "timeout" in data["stderr"].lower()
    
    def test_validate_code_all_languages(self, test_client: TestClient):
        """Test validating code for all supported languages."""
        languages = ["python", "javascript", "java", "cpp", "c", "go", "rust"]
        
        for language in languages:
            code_request = {
                "language": language,
                "code": "print('Hello')" if language != "javascript" else "console.log('Hello');"
            }
            
            response = test_client.post("/api/run/validate", json=code_request)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["language"] == language
            assert "valid" in data
            assert "warnings" in data
            assert "errors" in data
    
    def test_run_endpoints_response_format(self, test_client: TestClient):
        """Test response format consistency."""
        code_request = {
            "language": "python",
            "code": "print('Hello')",
            "stdin": "",
            "version": "3.11.0"
        }
        
        response = test_client.post("/api/run/", json=code_request)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        required_fields = ["stdout", "stderr", "exit_code", "execution_time", "memory_usage", "language", "version"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
    
    def test_run_endpoints_error_handling(self, test_client: TestClient):
        """Test run endpoints error handling."""
        # Test invalid JSON
        response = test_client.post("/api/run/", data="invalid json")
        assert response.status_code == 422
        
        response = test_client.post("/api/run/validate", data="invalid json")
        assert response.status_code == 422
        
        # Test with wrong HTTP method
        response = test_client.get("/api/run/")
        assert response.status_code == 405
        
        response = test_client.put("/api/run/")
        assert response.status_code == 405
        
        response = test_client.delete("/api/run/")
        assert response.status_code == 405
    
    @pytest.mark.asyncio
    async def test_run_endpoints_async(self, async_client: AsyncClient):
        """Test run endpoints with async client."""
        code_request = {
            "language": "python",
            "code": "print('Hello, World!')",
            "stdin": "",
            "version": "3.11.0"
        }
        
        response = await async_client.post("/api/run/", json=code_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["exit_code"] == 0
        assert "Hello, World!" in data["stdout"]
    
    def test_run_endpoints_response_time(self, test_client: TestClient):
        """Test run endpoints response time."""
        import time
        
        code_request = {
            "language": "python",
            "code": "print('Hello')",
            "stdin": "",
            "version": "3.11.0"
        }
        
        start_time = time.time()
        response = test_client.post("/api/run/", json=code_request)
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Response should be reasonably fast (< 2s for simple code)
        response_time = (end_time - start_time) * 1000
        assert response_time < 2000, f"Code execution took {response_time}ms, expected < 2000ms"
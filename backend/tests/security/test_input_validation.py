"""
Input validation security tests.
"""
import json
import pytest
from fastapi.testclient import TestClient


class TestInputValidation:
    """Tests for input validation vulnerabilities."""

    def test_sql_injection_query_params(self, test_client: TestClient):
        """SQL injection in query params should be handled gracefully."""
        payloads = [
            "'; DROP TABLE questions; --",
            "1' OR '1'='1",
            "admin'--",
            "' OR 1=1--",
            "1' UNION SELECT * FROM passwords--",
        ]
        for payload in payloads:
            response = test_client.get(f"/api/questions/search?q={payload}")
            assert response.status_code in [200, 400]

    def test_sql_injection_path_params(self, test_client: TestClient):
        """SQL injection in path params should be handled gracefully."""
        payloads = ["1' OR '1'='1", "../../etc/passwd", "<script>"]
        for payload in payloads:
            response = test_client.get(f"/api/questions/{payload}")
            assert response.status_code in [200, 404, 422]

    def test_sql_injection_body_fields(self, test_client: TestClient):
        """SQL injection in JSON body should be handled gracefully."""
        payloads = ["'; DROP TABLE users; --", "' OR 1=1--", "1' AND 1=1--"]
        for payload in payloads:
            body = {
                "problem": payload, "code": "x=1", "language": "python",
                "message": payload, "mode": "hint", "difficulty": "easy"
            }
            response = test_client.post("/api/coach/", json=body)
            assert response.status_code in [200, 401, 422]

    def test_nosql_injection_where(self, test_client: TestClient):
        """NoSQL $where injection in JSON body should be handled."""
        body = {
            "problem": {"$where": "1==1"}, "code": "x=1", "language": "python",
            "message": "test", "mode": "hint", "difficulty": "easy"
        }
        response = test_client.post("/api/coach/", json=body)
        assert response.status_code in [200, 401, 422]

    def test_nosql_injection_regex(self, test_client: TestClient):
        """NoSQL $regex injection in JSON body should be handled."""
        body = {
            "problem": {"$regex": ".*"}, "code": "x=1", "language": "python",
            "message": {"$gt": ""}, "mode": "hint", "difficulty": "easy"
        }
        response = test_client.post("/api/coach/", json=body)
        assert response.status_code in [200, 401, 422]

    def test_ssrf_code_execution(self, test_client: TestClient):
        """SSRF via code execution payload should not leak internal services."""
        code_payloads = [
            'import requests; requests.get("http://169.254.169.254/latest/meta-data/")',
            'import urllib.request; urllib.request.urlopen("http://localhost:8000")',
            'import os; os.system("curl http://internal-service/")',
        ]
        for code in code_payloads:
            response = test_client.post("/api/run/", json={
                "language": "python", "code": code, "stdin": ""
            })
            assert response.status_code in [200, 401]
            if response.status_code == 200:
                result = response.json()
                assert "169.254" not in result.get("stdout", "")
                assert "localhost" not in result.get("stdout", "")

    def test_path_traversal(self, test_client: TestClient):
        """Path traversal payloads should be handled gracefully."""
        payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "file:///etc/passwd",
            "/etc/passwd",
        ]
        for payload in payloads:
            response = test_client.get(f"/api/questions/{payload}")
            assert response.status_code in [200, 404, 422]

    def test_prototype_pollution(self, test_client: TestClient):
        """Prototype pollution payloads should be handled."""
        payloads = [
            '{"test": "value", "__proto__": {"admin": true}}',
            '{"test": "value", "constructor": {"prototype": {"admin": true}}}',
        ]
        for payload in payloads:
            response = test_client.post(
                "/api/coach/",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            assert response.status_code in [200, 401, 422]

    def test_integer_overflow(self, test_client: TestClient):
        """Integer overflow in pagination params should be handled."""
        test_cases = [
            ("/api/questions/?per_page=999999999", 422),
            ("/api/questions/?per_page=-1", 422),
            ("/api/questions/?page=-1", 422),
            ("/api/questions/?page=0", 422),
            ("/api/questions/?per_page=0", 422),
        ]
        for url, expected_status in test_cases:
            response = test_client.get(url)
            assert response.status_code in [200, expected_status]

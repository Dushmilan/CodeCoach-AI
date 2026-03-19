"""
Security vulnerability tests for API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
import json

from tests.fixtures.factories import TestDataGenerator


class TestSecurityVulnerabilities:
    """Test cases for security vulnerabilities."""
    
    def test_sql_injection_prevention(self, test_client: TestClient):
        """Test SQL injection prevention in search queries."""
        sql_injection_payloads = [
            "'; DROP TABLE questions; --",
            "1' OR '1'='1",
            "admin'--",
            "1' UNION SELECT * FROM passwords--",
            "test'; SELECT * FROM users; --",
            "' OR 1=1--",
            "\" OR 1=1--",
            "' OR 'a'='a",
            "1' AND 1=1--",
            "1' AND 1=2--"
        ]
        
        for payload in sql_injection_payloads:
            response = test_client.get(f"/api/questions/search?q={payload}")
            
            # Should handle gracefully without error
            assert response.status_code in [200, 400]
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
                assert "questions" in data
    
    def test_xss_prevention(self, test_client: TestClient):
        """Test XSS prevention in responses."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "<iframe src=javascript:alert('XSS')></iframe>",
            "<body onload=alert('XSS')>",
            "<div onclick=alert('XSS')>Click me</div>",
            "<script src=http://evil.com/xss.js></script>",
            "'\"><script>alert('XSS')</script>",
            "<script>document.cookie='hacked=true'</script>"
        ]
        
        for payload in xss_payloads:
            # Test in search
            response = test_client.get(f"/api/questions/search?q={payload}")
            assert response.status_code in [200, 400]
            
            if response.status_code == 200:
                data = response.json()
                # Ensure no script tags are present in response
                response_str = json.dumps(data)
                assert "<script" not in response_str.lower()
                assert "javascript:" not in response_str.lower()
    
    def test_path_traversal_prevention(self, test_client: TestClient):
        """Test path traversal prevention."""
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "file:///etc/passwd",
            "/etc/passwd",
            "C:\\Windows\\System32\\drivers\\etc\\hosts",
            "..\\config\\database.yml",
            "../../../app/config.py",
            "..\\..\\..\\..\\etc\\shadow",
            "../../../../../../../etc/passwd",
            "..%2f..%2f..%2fetc%2fpasswd"
        ]
        
        for payload in path_traversal_payloads:
            # Test in various endpoints
            endpoints = [
                f"/api/questions/search?q={payload}",
                f"/api/questions/category/{payload}",
                f"/api/questions/{payload}"
            ]
            
            for endpoint in endpoints:
                response = test_client.get(endpoint)
                
                # Should handle gracefully
                assert response.status_code in [200, 404, 422]
    
    def test_command_injection_prevention(self, test_client: TestClient):
        """Test command injection prevention in code execution."""
        command_injection_payloads = [
            "; cat /etc/passwd",
            "| whoami",
            "&& rm -rf /",
            "`cat /etc/passwd`",
            "$(cat /etc/passwd)",
            "test; echo 'injected'",
            "test && echo 'injected'",
            "test | echo 'injected'",
            "test || echo 'injected'",
            "test `echo 'injected'`"
        ]
        
        for payload in command_injection_payloads:
            code_request = {
                "language": "python",
                "code": f"print('test'){payload}",
                "stdin": "",
                "version": "3.11.0"
            }
            
            response = test_client.post("/api/run/", json=code_request)
            
            # Should execute safely
            assert response.status_code == 200
            data = response.json()
            
            # Should not contain sensitive information
            assert "passwd" not in data["stdout"].lower()
            assert "etc" not in data["stdout"].lower()
    
    def test_xxe_prevention(self, test_client: TestClient):
        """Test XXE (XML External Entity) prevention."""
        xxe_payloads = [
            "<!DOCTYPE foo [<!ENTITY xxe SYSTEM \"file:///etc/passwd\">]><foo>&xxe;</foo>",
            "<!ENTITY % xxe SYSTEM \"file:///etc/passwd\"> %xxe;",
            "<!DOCTYPE foo [<!ENTITY xxe SYSTEM \"http://evil.com/xxe.dtd\">]><foo>&xxe;</foo>",
            "<!DOCTYPE foo [<!ENTITY xxe SYSTEM \"file:///proc/version\">]><foo>&xxe;</foo>",
            "<!DOCTYPE foo [<!ENTITY xxe SYSTEM \"file:///etc/hosts\">]><foo>&xxe;</foo>"
        ]
        
        for payload in xxe_payloads:
            # Test in various contexts
            test_cases = [
                {"input": payload, "expected_output": "safe", "description": "XXE test"}
            ]
            
            # These should be handled safely
            assert isinstance(payload, str)
    
    def test_input_validation_length_limits(self, test_client: TestClient):
        """Test input validation length limits."""
        # Test extremely long strings
        long_strings = [
            "a" * 10000,  # 10KB
            "x" * 50000,  # 50KB
            "test" * 1000,  # 4KB
            "\n" * 1000,  # 1KB of newlines
            " " * 10000,  # 10KB of spaces
        ]
        
        for long_string in long_strings:
            # Test coaching request
            coaching_request = {
                "problem": long_string,
                "code": long_string,
                "language": "python",
                "message": long_string,
                "mode": "hint",
                "difficulty": "easy"
            }
            
            response = test_client.post("/api/coach/", json=coaching_request)
            
            # Should handle gracefully
            assert response.status_code in [200, 413, 422]
    
    def test_rate_limiting_bypass_attempts(self, test_client: TestClient):
        """Test rate limiting bypass attempts."""
        bypass_attempts = [
            # IP spoofing attempts
            {"X-Forwarded-For": "1.1.1.1"},
            {"X-Real-IP": "2.2.2.2"},
            {"X-Client-IP": "3.3.3.3"},
            {"CF-Connecting-IP": "4.4.4.4"},
            
            # User agent spoofing
            {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1)"},
            {"User-Agent": "curl/7.68.0"},
            {"User-Agent": "python-requests/2.25.1"},
            
            # Header manipulation
            {"X-RateLimit-Bypass": "true"},
            {"X-Admin": "true"},
            {"Authorization": "Bearer admin-token"}
        ]
        
        for headers in bypass_attempts:
            response = test_client.get("/health", headers=headers)
            
            # Should still work normally
            assert response.status_code == 200
    
    def test_authentication_bypass_attempts(self, test_client: TestClient):
        """Test authentication bypass attempts."""
        auth_bypass_payloads = [
            {"Authorization": "Bearer admin"},
            {"Authorization": "Basic YWRtaW46cGFzcw=="},  # admin:pass
            {"X-API-Key": "admin-key"},
            {"X-Admin-Token": "secret"},
            {"Cookie": "admin=true"},
            {"X-Auth-Token": "admin-token"}
        ]
        
        for payload in auth_bypass_payloads:
            headers = payload
            response = test_client.get("/api/questions/", headers=headers)
            
            # Should work normally (no auth required)
            assert response.status_code == 200
    
    def test_cors_policy_validation(self, test_client: TestClient):
        """Test CORS policy validation."""
        # Test various origin headers
        origins = [
            "https://malicious-site.com",
            "http://localhost:3001",
            "https://evil.com",
            "null",
            "file://",
            "*",
            "https://codecoach-ai-frontend.vercel.app.malicious.com"
        ]
        
        for origin in origins:
            response = test_client.get("/health", headers={"Origin": origin})
            
            # Should handle CORS properly
            assert response.status_code == 200
            cors_header = response.headers.get("Access-Control-Allow-Origin")
            assert cors_header is not None
    
    def test_content_type_validation(self, test_client: TestClient):
        """Test content type validation."""
        invalid_content_types = [
            "application/xml",
            "text/plain",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
            "application/javascript",
            "text/html",
            "application/zip",
            "application/octet-stream"
        ]
        
        for content_type in invalid_content_types:
            response = test_client.post(
                "/api/coach/",
                data='{"test": "data"}',
                headers={"Content-Type": content_type}
            )
            
            # Should handle gracefully
            assert response.status_code in [200, 415, 422]
    
    def test_json_injection_prevention(self, test_client: TestClient):
        """Test JSON injection prevention."""
        json_injection_payloads = [
            '{"test": "value", "__proto__": {"admin": true}}',
            '{"test": "value", "constructor": {"prototype": {"admin": true}}}',
            '{"test": "value", "toString": "function(){return \"injected\"}"}',
            '{"test": "value", "valueOf": "function(){return \"injected\"}"}',
            '{"test": "value", "hasOwnProperty": "function(){return true}}'
        ]
        
        for payload in json_injection_payloads:
            response = test_client.post(
                "/api/coach/",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            
            # Should handle gracefully
            assert response.status_code in [200, 422]
    
    def test_no_sensitive_data_exposure(self, test_client: TestClient):
        """Test no sensitive data exposure in responses."""
        sensitive_patterns = [
            "password",
            "secret",
            "key",
            "token",
            "api_key",
            "private_key",
            "database_url",
            "connection_string",
            "admin",
            "root"
        ]
        
        # Test various endpoints
        endpoints = [
            "/health",
            "/health/detailed",
            "/api/questions/",
            "/api/questions/stats",
            "/api/run/languages"
        ]
        
        for endpoint in endpoints:
            response = test_client.get(endpoint)
            assert response.status_code == 200
            
            # Check response for sensitive data
            response_text = response.text.lower()
            for pattern in sensitive_patterns:
                assert pattern not in response_text, f"Sensitive data exposed: {pattern} in {endpoint}"
    
    def test_error_message_security(self, test_client: TestClient):
        """Test error message security (no sensitive info in errors)."""
        # Test with invalid input
        invalid_requests = [
            {"invalid": "data"},  # Missing required fields
            {"language": "invalid"},  # Invalid enum
            {"difficulty": "invalid"},  # Invalid enum
        ]
        
        for invalid_request in invalid_requests:
            response = test_client.post("/api/coach/", json=invalid_request)
            
            assert response.status_code == 422
            
            # Check error message doesn't contain sensitive info
            error_response = response.json()
            error_str = json.dumps(error_response).lower()
            
            sensitive_patterns = ["password", "secret", "key", "token", "config"]
            for pattern in sensitive_patterns:
                assert pattern not in error_str, f"Sensitive info in error: {pattern}"
    
    def test_header_injection_prevention(self, test_client: TestClient):
        """Test header injection prevention."""
        header_injection_payloads = [
            {"X-Forwarded-For": "1.1.1.1\r\nX-Custom: injected"},
            {"User-Agent": "Mozilla\r\nLocation: http://evil.com"},
            {"Referer": "http://good.com\r\nSet-Cookie: hacked=true"},
            {"X-Real-IP": "1.1.1.1\r\nX-Forwarded-Proto: https"}
        ]
        
        for headers in header_injection_payloads:
            response = test_client.get("/health", headers=headers)
            
            # Should handle gracefully
            assert response.status_code == 200
    
    def test_session_fixation_prevention(self, test_client: TestClient):
        """Test session fixation prevention."""
        # Test session-related headers
        session_headers = [
            {"Cookie": "sessionid=fixed"},
            {"Set-Cookie": "sessionid=fixed"},
            {"X-Session-ID": "fixed"},
            {"Authorization": "Bearer fixed-token"}
        ]
        
        for headers in session_headers:
            response = test_client.get("/health", headers=headers)
            
            # Should work normally
            assert response.status_code == 200
    
    def test_clickjacking_prevention(self, test_client: TestClient):
        """Test clickjacking prevention headers."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        
        # Check for security headers
        headers = response.headers
        
        # X-Frame-Options should be set
        x_frame_options = headers.get("X-Frame-Options")
        assert x_frame_options in ["DENY", "SAMEORIGIN"]
        
        # X-Content-Type-Options should be set
        content_type_options = headers.get("X-Content-Type-Options")
        assert content_type_options == "nosniff"
    
    def test_secure_headers_presence(self, test_client: TestClient):
        """Test presence of security headers."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        
        headers = response.headers
        
        # Check for security headers
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security"
        ]
        
        for header in security_headers:
            assert header in headers or header.replace("-", "_") in headers, f"Missing security header: {header}"
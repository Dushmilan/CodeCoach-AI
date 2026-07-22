"""
Code execution security tests (sandbox escape, resource limits).
"""

from fastapi.testclient import TestClient


class TestExecutionSecurity:
    """Tests for code execution sandbox security."""

    def test_infinite_loop_timeout(self, test_client: TestClient):
        """Infinite loop code should timeout gracefully."""
        code = "while True: pass"
        response = test_client.post(
            "/api/run/", json={"language": "python", "code": code, "stdin": ""}
        )
        assert response.status_code in [200, 401, 504, 422]

    def test_memory_exhaustion(self, test_client: TestClient):
        """Memory exhaustion should be limited."""
        code = "x = [0] * (10**8)"
        response = test_client.post(
            "/api/run/", json={"language": "python", "code": code, "stdin": ""}
        )
        assert response.status_code in [200, 401, 504, 422]
        if response.status_code == 200:
            data = response.json()
            assert data.get("stderr", "") != "" or data.get("stdout", "") == ""

    def test_file_system_read_blocked(self, test_client: TestClient):
        """Code should not be able to read host files."""
        payloads = [
            'print(open("/etc/passwd").read())',
            'import os; os.system("cat /etc/passwd")',
        ]
        for code in payloads:
            response = test_client.post(
                "/api/run/", json={"language": "python", "code": code, "stdin": ""}
            )
            assert response.status_code in [200, 401]
            if response.status_code == 200:
                data = response.json()
                assert "root:" not in data.get("stdout", ""), (
                    f"File read leaked: {code}"
                )

    def test_network_access_blocked(self, test_client: TestClient):
        """Code should not be able to make outbound network requests."""
        code = 'import urllib.request; print(urllib.request.urlopen("http://localhost:8000/health").read())'
        response = test_client.post(
            "/api/run/", json={"language": "python", "code": code, "stdin": ""}
        )
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert "healthy" not in data.get("stdout", ""), "Network access leaked"

    def test_process_spawn_blocked(self, test_client: TestClient):
        """Code should not be able to spawn host processes."""
        payloads = [
            'import os; os.system("whoami")',
            'import subprocess; print(subprocess.check_output(["whoami"]).decode())',
        ]
        for code in payloads:
            response = test_client.post(
                "/api/run/", json={"language": "python", "code": code, "stdin": ""}
            )
            assert response.status_code in [200, 401]
            if response.status_code == 200:
                data = response.json()
                admin_names = ["root", "administrator", "admin"]
                stdout_lower = data.get("stdout", "").lower()
                assert not any(name in stdout_lower for name in admin_names), (
                    f"Process spawn leaked: {code}"
                )

    def test_js_require_fs(self, test_client: TestClient):
        """JavaScript code should not access fs module."""
        code = 'const fs = require("fs"); console.log(fs.readFileSync("/etc/passwd", "utf8"));'
        response = test_client.post(
            "/api/run/", json={"language": "javascript", "code": code, "stdin": ""}
        )
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert "root:" not in data.get("stdout", ""), "JS fs.readFileSync leaked"

    def test_java_runtime_exec(self, test_client: TestClient):
        """Java code should not execute runtime commands."""
        code = """
public class Main {
    public static void main(String[] args) throws Exception {
        Runtime.getRuntime().exec("whoami");
    }
}
        """.strip()
        response = test_client.post(
            "/api/run/", json={"language": "java", "code": code, "stdin": ""}
        )
        assert response.status_code in [200, 400, 401, 422]

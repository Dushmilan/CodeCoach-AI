"""Security test fixtures.

Sets environment variables required for the app to construct service
dependencies (e.g. the NIM provider needs an API key to be present) so that
security tests exercise the actual request handling paths rather than failing
with a 500 during dependency construction.
"""

import os
import pytest


@pytest.fixture(autouse=True)
def _security_env():
    """Ensure NIM provider construction succeeds during security tests."""
    os.environ["NVIDIA_API_KEY"] = "test_nvidia_key_for_security_tests"
    os.environ["PISTON_API_URL"] = "http://127.0.0.1:2000/api/v2"
    yield

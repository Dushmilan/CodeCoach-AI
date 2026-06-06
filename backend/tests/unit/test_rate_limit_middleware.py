import pytest
import time


class TestRateLimitMiddleware:
    def test_is_rate_limited_under_limit(self):
        from app.middleware.rate_limit import RateLimitMiddleware
        middleware = RateLimitMiddleware()

        result = middleware.is_rate_limited("127.0.0.1", "5/minute")
        assert result is False

    def test_is_rate_limited_exact_limit(self):
        from app.middleware.rate_limit import RateLimitMiddleware
        middleware = RateLimitMiddleware()

        for _ in range(5):
            middleware.is_rate_limited("127.0.0.1", "5/minute")
        result = middleware.is_rate_limited("127.0.0.1", "5/minute")
        assert result is True

    def test_is_rate_limited_different_keys(self):
        from app.middleware.rate_limit import RateLimitMiddleware
        middleware = RateLimitMiddleware()

        for _ in range(5):
            middleware.is_rate_limited("user-a", "5/minute")
        assert middleware.is_rate_limited("user-a", "5/minute") is True
        assert middleware.is_rate_limited("user-b", "5/minute") is False

    def test_is_rate_limited_window_expires(self):
        from unittest.mock import patch
        from app.middleware.rate_limit import RateLimitMiddleware
        middleware = RateLimitMiddleware()

        for _ in range(5):
            middleware.is_rate_limited("127.0.0.1", "5/minute")

        mock_now = time.time() + 61
        with patch("app.middleware.rate_limit.time.time", return_value=mock_now):
            result = middleware.is_rate_limited("127.0.0.1", "5/minute")
            assert result is False

    def test_parse_time_window_minute(self):
        from app.middleware.rate_limit import RateLimitMiddleware
        middleware = RateLimitMiddleware()
        assert middleware._parse_time_window("minute") == 60

    def test_parse_time_window_hour(self):
        from app.middleware.rate_limit import RateLimitMiddleware
        middleware = RateLimitMiddleware()
        assert middleware._parse_time_window("hour") == 3600

    def test_parse_time_window_second(self):
        from app.middleware.rate_limit import RateLimitMiddleware
        middleware = RateLimitMiddleware()
        assert middleware._parse_time_window("second") == 1

    def test_parse_time_window_day(self):
        from app.middleware.rate_limit import RateLimitMiddleware
        middleware = RateLimitMiddleware()
        assert middleware._parse_time_window("day") == 86400

    def test_parse_time_window_custom_format(self):
        from app.middleware.rate_limit import RateLimitMiddleware
        middleware = RateLimitMiddleware()
        assert middleware._parse_time_window("1m") == 60
        assert middleware._parse_time_window("5h") == 18000
        assert middleware._parse_time_window("30s") == 30

    def test_parse_time_window_default(self):
        from app.middleware.rate_limit import RateLimitMiddleware
        middleware = RateLimitMiddleware()
        assert middleware._parse_time_window("unknown") == 60

    def test_get_rate_limit_info(self):
        from app.middleware.rate_limit import RateLimitMiddleware
        middleware = RateLimitMiddleware()

        middleware.is_rate_limited("127.0.0.1", "10/minute")
        middleware.is_rate_limited("127.0.0.1", "10/minute")
        info = middleware.get_rate_limit_info("127.0.0.1")

        assert info["requests"] == 2

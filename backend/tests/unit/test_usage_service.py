"""Unit tests for UsageService — token metering + daily cap math."""

from datetime import date

import pytest

from app.models.usage_schemas import DailyUsage
from app.services.usage_service import (
    UsageService,
    check_caps,
    usage_headers,
)


class FakeUsageRepo:
    def __init__(self):
        self.events = []
        self.daily = {}

    async def add_event(self, **kwargs):
        self.events.append(kwargs)

    async def increment_daily(
        self, *, user_id, usage_date, input_tokens, output_tokens
    ):
        key = (user_id, usage_date)
        cur_in, cur_out = self.daily.get(key, (0, 0))
        self.daily[key] = (cur_in + input_tokens, cur_out + output_tokens)

    async def get_daily(self, user_id, usage_date):
        key = (user_id, usage_date)
        if key not in self.daily:
            return None
        cur_in, cur_out = self.daily[key]
        return DailyUsage(
            user_id=user_id,
            usage_date=usage_date,
            input_tokens=cur_in,
            output_tokens=cur_out,
        )


@pytest.fixture
def service():
    return UsageService(repo=FakeUsageRepo())


class TestUsageServiceRecord:
    @pytest.mark.asyncio
    async def test_record_appends_event_and_increments_daily(self, service):
        await service.record(
            user_id="user-1",
            provider="groq",
            model="llama-3.3-70b-versatile",
            endpoint="coach",
            input_tokens=10,
            output_tokens=20,
        )
        await service.record(
            user_id="user-1",
            provider="groq",
            model="llama-3.1-8b-instant",
            endpoint="coach",
            input_tokens=5,
            output_tokens=7,
        )

        assert len(service.repo.events) == 2
        assert service.repo.events[0]["provider"] == "groq"
        daily = await service.get_daily_usage("user-1")
        assert daily.input_tokens == 15
        assert daily.output_tokens == 27

    @pytest.mark.asyncio
    async def test_get_daily_usage_missing_returns_zeros(self, service):
        daily = await service.get_daily_usage("nobody")
        assert daily.input_tokens == 0
        assert daily.output_tokens == 0


class TestCheckCaps:
    def _daily(self, input_tokens=0, output_tokens=0):
        return DailyUsage(
            user_id="u",
            usage_date=date(2026, 1, 1),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    def test_under_cap_allowed(self):
        allowed, rem_in, rem_out = check_caps(self._daily(10, 5), 100, 50)
        assert allowed is True
        assert rem_in == 90
        assert rem_out == 45

    def test_input_at_cap_blocked(self):
        allowed, rem_in, _ = check_caps(self._daily(100, 5), 100, 50)
        assert allowed is False
        assert rem_in == 0

    def test_output_at_cap_blocked(self):
        allowed, _, rem_out = check_caps(self._daily(10, 50), 100, 50)
        assert allowed is False
        assert rem_out == 0

    def test_over_cap_clamps_remaining_to_zero(self):
        allowed, rem_in, rem_out = check_caps(self._daily(200, 99), 100, 50)
        assert allowed is False
        assert rem_in == 0
        assert rem_out == 0

    def test_zero_usage_fully_allowed(self):
        allowed, rem_in, rem_out = check_caps(self._daily(0, 0), 100, 50)
        assert allowed is True
        assert rem_in == 100
        assert rem_out == 50


class TestUsageHeaders:
    def test_headers_include_used_remaining_and_reset(self):
        daily = DailyUsage(
            user_id="u",
            usage_date=date(2026, 1, 1),
            input_tokens=10,
            output_tokens=5,
        )
        headers = usage_headers(daily, input_cap=100, output_cap=50)
        assert headers["X-Usage-Input"] == "10"
        assert headers["X-Usage-Output"] == "5"
        assert headers["X-Usage-Remaining-Input"] == "90"
        assert headers["X-Usage-Remaining-Output"] == "45"
        assert "X-Usage-Reset" in headers

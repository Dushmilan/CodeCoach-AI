"""Unit tests for UsageService — token metering (recording only)."""

import pytest

from app.models.usage_schemas import DailyUsage
from app.services.usage_service import UsageService


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
            model="openai/gpt-oss-120b",
            endpoint="coach",
            input_tokens=10,
            output_tokens=20,
        )
        await service.record(
            user_id="user-1",
            provider="groq",
            model="openai/gpt-oss-20b",
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

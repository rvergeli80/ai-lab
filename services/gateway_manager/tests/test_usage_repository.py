from datetime import datetime, timedelta, timezone

from gateway_manager.usage import (
    SQLiteUsageRepository,
    UsageRecord,
)


def test_usage_repository(tmp_path):

    repository = SQLiteUsageRepository(
        tmp_path / "usage.db"
    )

    record = UsageRecord.create(
        provider="ollama",
        model="laguna-xs-2.1",
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        cost_eur=0.0,
        latency_ms=1200,
        capability="coding",
    )

    repository.add(record)

    now = datetime.now(timezone.utc)

    records = repository.list_between(
        now - timedelta(minutes=1),
        now + timedelta(minutes=1),
    )

    assert len(records) == 1
    assert records[0].provider == "ollama"
    assert records[0].total_tokens == 150

    cost = repository.total_cost_between(
        now - timedelta(minutes=1),
        now + timedelta(minutes=1),
    )

    assert cost == 0.0

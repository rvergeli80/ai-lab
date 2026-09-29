from datetime import (
    datetime,
    timedelta,
    timezone,
)

from gateway_manager.usage import (
    SQLiteUsageRepository,
    UsageRecord,
)


def test_usage_repository(
    tmp_path,
):

    repository = SQLiteUsageRepository(
        tmp_path / "usage.db"
    )

    record = UsageRecord.create(
        provider="openrouter",
        model="openrouter-gemma",
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        cost_amount=0.25,
        cost_currency="USD",
        latency_ms=1200,
        capability="coding",
    )

    repository.add(
        record
    )

    now = datetime.now(
        timezone.utc
    )

    start = (
        now
        - timedelta(minutes=1)
    )

    end = (
        now
        + timedelta(minutes=1)
    )

    records = (
        repository.list_between(
            start,
            end,
        )
    )

    assert len(records) == 1

    stored = records[0]

    assert (
        stored.provider
        == "openrouter"
    )

    assert (
        stored.model
        == "openrouter-gemma"
    )

    assert stored.total_tokens == 150

    assert (
        stored.cost_amount
        == 0.25
    )

    assert (
        stored.cost_currency
        == "USD"
    )

    usd_cost = (
        repository
        .total_cost_between(
            start=start,
            end=end,
            currency="USD",
        )
    )

    eur_cost = (
        repository
        .total_cost_between(
            start=start,
            end=end,
            currency="EUR",
        )
    )

    assert usd_cost == 0.25
    assert eur_cost == 0.0

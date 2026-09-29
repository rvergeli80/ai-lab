from gateway_manager.adapters.dto import ProviderResponse
from gateway_manager.domain import Request
from gateway_manager.runtime import Gateway
from gateway_manager.usage import SQLiteUsageRepository


def test_gateway_records_successful_usage(
    tmp_path,
    monkeypatch,
):
    repository = SQLiteUsageRepository(
        tmp_path / "usage.db"
    )

    gateway = Gateway(
        usage_repository=repository
    )

    def fake_complete(
        model_name,
        request,
    ):
        return ProviderResponse(
            content="TEST OK",
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            finish_reason="stop",
        )

    monkeypatch.setattr(
        gateway.ollama_adapter,
        "complete",
        fake_complete,
    )

    response = gateway.complete(
        Request(
            model="laguna-xs-2.1",
            prompt="test",
            capability="coding",
            project="ai-lab-test",
            tenant="test-tenant",
            think=False,
        )
    )

    assert response.content == "TEST OK"
    assert response.usage is not None
    assert response.usage.total_tokens == 15

    records = repository.list_between(
        response_timestamp_start(),
        response_timestamp_end(),
    )

    assert len(records) == 1

    record = records[0]

    assert record.provider == "ollama"
    assert record.model == "laguna-xs-2.1"
    assert record.prompt_tokens == 10
    assert record.completion_tokens == 5
    assert record.total_tokens == 15
    assert record.cost_eur == 0.0
    assert record.capability == "coding"
    assert record.project == "ai-lab-test"
    assert record.tenant == "test-tenant"
    assert record.success is True
    assert record.fallback is False


def response_timestamp_start():
    from datetime import (
        datetime,
        timedelta,
        timezone,
    )

    return (
        datetime.now(timezone.utc)
        - timedelta(minutes=1)
    )


def response_timestamp_end():
    from datetime import (
        datetime,
        timedelta,
        timezone,
    )

    return (
        datetime.now(timezone.utc)
        + timedelta(minutes=1)
    )

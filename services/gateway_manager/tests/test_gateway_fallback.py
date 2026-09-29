from datetime import (
    datetime,
    timedelta,
    timezone,
)

from gateway_manager.adapters.dto import ProviderResponse
from gateway_manager.budget import BudgetPolicy
from gateway_manager.domain import Request
from gateway_manager.runtime import Gateway
from gateway_manager.usage import SQLiteUsageRepository


def test_remote_failure_falls_back_to_local_and_records_both_attempts(
    tmp_path,
    monkeypatch,
):

    repository = SQLiteUsageRepository(
        tmp_path / "usage.db"
    )

    gateway = Gateway(
        usage_repository=repository
    )

    gateway.router.budget = BudgetPolicy(
        usage_repository=repository
    )

    monkeypatch.setattr(
        gateway.availability,
        "available",
        lambda: {
            "openrouter",
            "ollama",
        },
    )

    def failing_remote(
        model_name,
        request,
    ):
        raise RuntimeError(
            "insufficient credits"
        )

    def successful_local(
        model_name,
        request,
    ):
        return ProviderResponse(
            content="FALLBACK LOCAL OK",
            prompt_tokens=20,
            completion_tokens=5,
            total_tokens=25,
            finish_reason="stop",
        )

    monkeypatch.setattr(
        gateway.litellm_adapter,
        "complete",
        failing_remote,
    )

    monkeypatch.setattr(
        gateway.ollama_adapter,
        "complete",
        successful_local,
    )

    response = gateway.complete(
        Request(
            capability="coding",
            prompt="test fallback",
            project="ai-lab-test",
            tenant="test-tenant",
        )
    )

    assert response.content == "FALLBACK LOCAL OK"
    assert response.provider == "ollama"
    assert response.model == "laguna-xs-2.1"

    now = datetime.now(
        timezone.utc
    )

    records = repository.list_between(
        now - timedelta(minutes=1),
        now + timedelta(minutes=1),
    )

    assert len(records) == 2

    failed = records[0]
    successful = records[1]

    assert failed.provider == "openrouter"
    assert failed.model == "openrouter-gemma"
    assert failed.success is False
    assert failed.fallback is False
    assert failed.error_type == "RuntimeError"

    assert successful.provider == "ollama"
    assert successful.model == "laguna-xs-2.1"
    assert successful.success is True
    assert successful.fallback is True

    assert successful.prompt_tokens == 20
    assert successful.completion_tokens == 5
    assert successful.total_tokens == 25

    assert successful.cost_amount == 0.0
    assert successful.cost_currency == "EUR"

    assert successful.project == "ai-lab-test"
    assert successful.tenant == "test-tenant"

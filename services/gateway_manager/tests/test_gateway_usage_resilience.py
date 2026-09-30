from datetime import datetime

from gateway_manager.adapters.dto import (
    ProviderResponse,
)
from gateway_manager.domain import Request
from gateway_manager.runtime import Gateway
from gateway_manager.usage import (
    UsageRecord,
    UsageRepository,
)


class FailingUsageRepository(
    UsageRepository
):

    def add(
        self,
        record: UsageRecord,
    ) -> None:

        raise RuntimeError(
            "usage storage unavailable"
        )

    def list_between(
        self,
        start: datetime,
        end: datetime,
    ) -> list[UsageRecord]:

        return []

    def total_cost_between(
        self,
        start: datetime,
        end: datetime,
        currency: str,
    ) -> float:

        return 0.0


def test_usage_failure_does_not_break_inference(
    monkeypatch,
):

    repository = (
        FailingUsageRepository()
    )

    gateway = Gateway(
        usage_repository=repository
    )

    def fake_complete(
        model_name,
        request,
    ):

        return ProviderResponse(
            content="INFERENCE OK",
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
            think=False,
        )
    )

    assert (
        response.content
        == "INFERENCE OK"
    )

    assert response.usage is not None

    assert (
        response.usage.total_tokens
        == 15
    )

from pathlib import Path

import pytest

from gateway_manager.budget import (
    BudgetPolicy,
)
from gateway_manager.domain import Request
from gateway_manager.runtime import Gateway
from gateway_manager.usage import (
    SQLiteUsageRepository,
    UsageRecord,
)


def test_explicit_model_cannot_bypass_budget(
    tmp_path,
):

    repository = SQLiteUsageRepository(
        Path(tmp_path)
        / "usage.db"
    )

    repository.add(
        UsageRecord.create(
            provider="openai",
            model="gpt-5",
            cost_amount=2.0,
            cost_currency="USD",
            success=True,
        )
    )

    gateway = Gateway(
        usage_repository=repository
    )

    gateway.router.budget = (
        BudgetPolicy(
            usage_repository=repository
        )
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "not allowed by "
            "current budget policy"
        ),
    ):

        gateway.complete(
            Request(
                model="gpt-5",
                prompt="test",
            )
        )

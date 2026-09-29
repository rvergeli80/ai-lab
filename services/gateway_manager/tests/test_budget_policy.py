from gateway_manager.budget import (
    BudgetPolicy,
)
from gateway_manager.registry.model_registry import (
    ModelRegistry,
)
from gateway_manager.usage import (
    SQLiteUsageRepository,
    UsageRecord,
)


def test_budget_blocks_premium_model(
    tmp_path,
):

    repository = SQLiteUsageRepository(
        tmp_path / "usage.db"
    )

    repository.add(
        UsageRecord.create(
            provider="openai",
            model="gpt-5",
            cost_amount=2.00,
            cost_currency="USD",
            success=True,
        )
    )

    policy = BudgetPolicy(
        usage_repository=repository
    )

    registry = ModelRegistry.load()

    model = registry.get(
        "gpt-5"
    )

    assert model is not None

    assert (
        policy.allows(model)
        is False
    )


def test_budget_keeps_local_available(
    tmp_path,
):

    repository = SQLiteUsageRepository(
        tmp_path / "usage.db"
    )

    repository.add(
        UsageRecord.create(
            provider="openai",
            model="gpt-5",
            cost_amount=100.00,
            cost_currency="USD",
            success=True,
        )
    )

    policy = BudgetPolicy(
        usage_repository=repository
    )

    registry = ModelRegistry.load()

    model = registry.get(
        "laguna-xs-2.1"
    )

    assert model is not None

    assert (
        policy.allows(model)
        is True
    )

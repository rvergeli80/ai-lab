from datetime import (
    datetime,
    timezone,
)
from pathlib import Path

import yaml

from gateway_manager.domain import Model
from gateway_manager.usage import (
    SQLiteUsageRepository,
    UsageRepository,
)


def find_lab_root(
    start: Path,
) -> Path:

    current = start.resolve()

    while current != current.parent:

        if (
            current
            / "lab.yaml"
        ).exists():
            return current

        current = current.parent

    raise RuntimeError(
        "No se encontró la raíz del LAB (lab.yaml)"
    )


ROOT = find_lab_root(
    Path(__file__)
)

BUDGET_FILE = (
    ROOT
    / "config"
    / "budget"
    / "budgets.yaml"
)

DEFAULT_USAGE_DB = (
    ROOT
    / "runtime"
    / "gateway"
    / "usage.db"
)


class BudgetPolicy:

    def __init__(
        self,
        usage_repository: UsageRepository
        | None = None,
    ) -> None:

        with BUDGET_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:

            self.config = (
                yaml.safe_load(file)
                or {}
            )

        self.usage_repository = (
            usage_repository
            or SQLiteUsageRepository(
                DEFAULT_USAGE_DB
            )
        )

    def allows(
        self,
        model: Model,
    ) -> bool:

        budget = self.config.get(
            "budget",
            {},
        )

        if not budget.get(
            "enabled",
            True,
        ):
            return True

        tier = self._tier(
            model
        )

        tier_config = (
            budget
            .get(
                "tiers",
                {},
            )
            .get(
                tier,
                {},
            )
        )

        if not tier_config.get(
            "enabled",
            True,
        ):
            return False

        if not tier_config.get(
            "enforce_budget",
            False,
        ):
            return True

        return self._within_budget()

    def _within_budget(
        self,
    ) -> bool:

        budget = self.config.get(
            "budget",
            {},
        )

        defaults = budget.get(
            "default",
            {},
        )

        currency = budget.get(
            "currency",
            "USD",
        )

        daily_limit = float(
            defaults.get(
                "daily",
                0.0,
            )
        )

        monthly_limit = float(
            defaults.get(
                "monthly",
                0.0,
            )
        )

        now = datetime.now(
            timezone.utc
        )

        day_start = now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        month_start = now.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        daily_spend = (
            self.usage_repository
            .total_cost_between(
                start=day_start,
                end=now,
                currency=currency,
            )
        )

        monthly_spend = (
            self.usage_repository
            .total_cost_between(
                start=month_start,
                end=now,
                currency=currency,
            )
        )

        if (
            daily_limit > 0
            and daily_spend
            >= daily_limit
        ):
            return False

        if (
            monthly_limit > 0
            and monthly_spend
            >= monthly_limit
        ):
            return False

        return True

    @staticmethod
    def _tier(
        model: Model,
    ) -> str:

        if (
            model.provider
            == "ollama"
            or model.has_tag(
                "local"
            )
        ):
            return "local"

        if model.has_tag(
            "premium"
        ):
            return "premium"

        if model.has_tag(
            "free"
        ):
            return "free"

        return "paid"

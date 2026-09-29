from pathlib import Path

import yaml

from gateway_manager.domain import Model


def find_lab_root(start: Path) -> Path:
    current = start.resolve()

    while current != current.parent:
        if (current / "lab.yaml").exists():
            return current
        current = current.parent

    raise RuntimeError(
        "No se encontró la raíz del LAB (lab.yaml)"
    )


ROOT = find_lab_root(Path(__file__))

BUDGET_FILE = ROOT / "config/budget/budgets.yaml"


class BudgetPolicy:

    def __init__(self) -> None:
        with BUDGET_FILE.open(
            "r",
            encoding="utf-8",
        ) as f:
            self.config = yaml.safe_load(f) or {}

    def allows(
        self,
        model: Model,
    ) -> bool:

        budget = self.config.get("budget", {})

        if not budget.get("enabled", True):
            return True

        tier = self._tier(model)

        tier_config = (
            budget
            .get("tiers", {})
            .get(tier, {})
        )

        return tier_config.get(
            "enabled",
            True,
        )

    @staticmethod
    def _tier(model: Model) -> str:

        if (
            model.provider == "ollama"
            or model.has_tag("local")
        ):
            return "local"

        if model.has_tag("premium"):
            return "premium"

        if model.has_tag("free"):
            return "free"

        return "paid"

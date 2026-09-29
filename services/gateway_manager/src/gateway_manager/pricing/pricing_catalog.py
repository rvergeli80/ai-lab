from dataclasses import dataclass
from pathlib import Path

import yaml


def find_lab_root(start: Path) -> Path:
    current = start.resolve()

    while current != current.parent:
        if (current / "lab.yaml").exists():
            return current

        current = current.parent

    raise RuntimeError(
        "No se encontró la raíz del LAB (lab.yaml)"
    )


LAB_ROOT = find_lab_root(Path(__file__))

PRICING_FILE = (
    LAB_ROOT
    / "config"
    / "pricing"
    / "models.yaml"
)


@dataclass(frozen=True, slots=True)
class ModelPricing:
    input_per_million: float | None
    output_per_million: float | None
    currency: str


class PricingCatalog:

    def __init__(self) -> None:
        self._prices = self._load()

    def _load(
        self,
    ) -> dict[str, ModelPricing]:

        with PRICING_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = yaml.safe_load(file) or {}

        default_currency = data.get(
            "currency",
            "EUR",
        )

        models = data.get(
            "models",
            {},
        )

        prices: dict[str, ModelPricing] = {}

        for model_name, config in models.items():
            prices[model_name] = ModelPricing(
                input_per_million=(
                    config.get(
                        "input_per_million"
                    )
                ),
                output_per_million=(
                    config.get(
                        "output_per_million"
                    )
                ),
                currency=(
                    config.get(
                        "currency",
                        default_currency,
                    )
                ),
            )

        return prices

    def get(
        self,
        model_name: str,
    ) -> ModelPricing | None:

        return self._prices.get(
            model_name
        )

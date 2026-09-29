from dataclasses import dataclass

from litellm import cost_per_token

from .pricing_catalog import PricingCatalog


@dataclass(
    frozen=True,
    slots=True,
)
class PricingQuote:
    amount: float
    currency: str
    source: str


class PricingService:

    def __init__(
        self,
        catalog: PricingCatalog | None = None,
    ) -> None:

        self.catalog = (
            catalog
            or PricingCatalog()
        )

    def calculate_cost(
        self,
        *,
        canonical_model_name: str,
        provider: str,
        litellm_model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> PricingQuote | None:

        configured = self.catalog.get(
            canonical_model_name
        )

        if (
            configured is not None
            and configured.input_per_million
            is not None
            and configured.output_per_million
            is not None
        ):
            input_cost = (
                prompt_tokens
                / 1_000_000
                * configured.input_per_million
            )

            output_cost = (
                completion_tokens
                / 1_000_000
                * configured.output_per_million
            )

            return PricingQuote(
                amount=(
                    input_cost
                    + output_cost
                ),
                currency=configured.currency,
                source="nevermine-config",
            )

        if provider == "ollama":
            return None

        try:
            (
                input_cost,
                output_cost,
            ) = cost_per_token(
                model=litellm_model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=(
                    completion_tokens
                ),
            )

        except Exception:
            return None

        return PricingQuote(
            amount=(
                float(input_cost)
                + float(output_cost)
            ),
            currency="USD",
            source="litellm",
        )

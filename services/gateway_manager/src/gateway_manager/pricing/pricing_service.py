from .pricing_catalog import PricingCatalog


class PricingService:

    def __init__(
        self,
        catalog: PricingCatalog | None = None,
    ) -> None:

        self.catalog = (
            catalog
            or PricingCatalog()
        )

    def calculate_cost_eur(
        self,
        *,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float | None:

        pricing = self.catalog.get(
            model_name
        )

        if pricing is None:
            return None

        if (
            pricing.input_per_million_eur
            is None
            or pricing.output_per_million_eur
            is None
        ):
            return None

        input_cost = (
            prompt_tokens
            / 1_000_000
            * pricing.input_per_million_eur
        )

        output_cost = (
            completion_tokens
            / 1_000_000
            * pricing.output_per_million_eur
        )

        return (
            input_cost
            + output_cost
        )

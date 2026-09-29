from gateway_manager.availability import ProviderAvailability
from gateway_manager.budget import BudgetPolicy
from gateway_manager.domain import Model
from gateway_manager.registry.model_registry import ModelRegistry

from .policy_loader import PolicyLoader


class FallbackRouter:
    """
    Construye la cadena ordenada de modelos candidatos
    teniendo en cuenta:

    - capability
    - disponibilidad del proveedor
    - tier
    - prioridad
    - política de presupuesto
    """

    def __init__(
        self,
        registry: ModelRegistry,
        availability: ProviderAvailability,
        budget: BudgetPolicy | None = None,
    ):
        self.registry = registry
        self.availability = availability
        self.budget = budget or BudgetPolicy()
        self.config = PolicyLoader.load()

    def route(
        self,
        capability: str,
    ) -> list[Model]:

        policy = self.config["policies"].get(capability)

        if policy is None:
            raise RuntimeError(
                f"No routing policy defined for capability: {capability}"
            )

        available_providers = self.availability.available()

        models = [
            model
            for model in self.registry.list_enabled().values()
            if (
                model.provider in available_providers
                and model.has_capability(capability)
                and self.budget.allows(model)
            )
        ]

        candidates: list[Model] = []

        for tier_config in policy.get("candidates", []):
            tier = tier_config["tier"]

            tier_models = [
                model
                for model in models
                if self._tier(model) == tier
            ]

            tier_models.sort(
                key=lambda model: model.priority,
                reverse=True,
            )

            candidates.extend(tier_models)

        return candidates

    def max_attempts(self) -> int:
        return int(
            self.config
            .get("fallback", {})
            .get("max_attempts", 4)
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

from gateway_manager.availability import ProviderAvailability
from gateway_manager.budget import BudgetPolicy
from gateway_manager.registry.model_registry import ModelRegistry
from gateway_manager.routing import FallbackRouter
from gateway_manager.selection.selection_engine import SelectionEngine


def run(
    capability: str | None,
    tag: str | None,
) -> None:

    registry = ModelRegistry.load()
    availability = ProviderAvailability()
    budget = BudgetPolicy()

    if capability is not None:

        router = FallbackRouter(
            registry=registry,
            availability=availability,
            budget=budget,
        )

        candidates = router.route(
            capability
        )

        if tag is not None:
            candidates = [
                model
                for model in candidates
                if model.has_tag(tag)
            ]

        if not candidates:
            print(
                "No matching model found"
            )
            return

        model = candidates[0]

        print(model.name)
        return

    selector = SelectionEngine(
        registry
    )

    model = selector.select(
        tag=tag,
        available_providers=(
            availability.available()
        ),
    )

    if (
        model is not None
        and not budget.allows(model)
    ):
        model = None

    if model is None:
        print(
            "No matching model found"
        )
        return

    print(model.name)

from gateway_manager.registry.model_registry import ModelRegistry
from gateway_manager.selection.selection_engine import SelectionEngine


def run(capability: str | None, tag: str | None):

    registry = ModelRegistry.load()

    selector = SelectionEngine(registry)

    model = selector.select(
        capability=capability,
        tag=tag,
    )

    if model is None:
        print("No matching model found")
        return

    print(model.name)
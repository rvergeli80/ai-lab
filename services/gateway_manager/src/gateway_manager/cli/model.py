from gateway_manager.registry.model_registry import ModelRegistry


def run(name: str):

    registry = ModelRegistry.load()

    model = registry.get(name)

    if model is None:
        print(f"Model '{name}' not found")
        return

    print(model)
from gateway_manager.registry.model_registry import ModelRegistry


def run():

    registry = ModelRegistry.load()

    for model in registry.list_enabled().values():
        print(model.name)
from gateway_manager.registry.model_registry import ModelRegistry


def test_registry_loads_enabled_models():

    registry = ModelRegistry.load()

    models = registry.list_enabled()

    assert "gpt-5" in models
    assert "gpt-5-mini" in models
    assert "openrouter-gemma" in models
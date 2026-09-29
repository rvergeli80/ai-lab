from gateway_manager.registry.model_registry import ModelRegistry
from gateway_manager.selection.selection_engine import SelectionEngine


def test_select_chat_model():

    registry = ModelRegistry.load()

    selector = SelectionEngine(registry)

    model = selector.select(capability="chat")

    assert model is not None
    assert model.name == "gpt-5"


def test_select_unknown_capability():

    registry = ModelRegistry.load()

    selector = SelectionEngine(registry)

    assert selector.select(capability="foobar") is None
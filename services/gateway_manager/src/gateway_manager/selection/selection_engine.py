from gateway_manager.domain import Model
from gateway_manager.registry.model_registry import ModelRegistry


class SelectionEngine:
    """Selecciona el modelo más adecuado según unos criterios."""

    def __init__(self, registry: ModelRegistry):
        self.registry = registry

    def select(
        self,
        capability: str | None = None,
        tag: str | None = None,
        available_providers: set[str] | None = None,
    ) -> Model | None:

        models = self.registry.list_enabled().values()

        if capability:
            models = [
                m for m in models
                if m.has_capability(capability)
            ]

        if tag:
            models = [
                m for m in models
                if m.has_tag(tag)
            ]

        if available_providers is not None:
            models = [
                m for m in models
                if m.provider in available_providers
            ]

        models = sorted(
            models,
            key=lambda m: m.priority,
            reverse=True,
        )

        if not models:
            return None

        return models[0]
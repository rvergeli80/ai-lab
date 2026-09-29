from dataclasses import dataclass


@dataclass(slots=True)
class Model:
    """Entidad de dominio que representa un modelo del catálogo."""

    name: str
    provider: str
    provider_model: str
    status: str
    capabilities: list[str]
    context_window: int
    priority: int
    tags: list[str]

    @property
    def enabled(self) -> bool:
        return self.status == "enabled"

    def has_capability(self, capability: str) -> bool:
        return capability in self.capabilities

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags
    

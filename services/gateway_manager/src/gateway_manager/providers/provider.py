from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Provider:
    """Entidad de dominio que representa un proveedor."""

    name: str
    env: str
    prefix: str

    def build_model_name(self, model: str) -> str:
        return f"{self.prefix}/{model}"
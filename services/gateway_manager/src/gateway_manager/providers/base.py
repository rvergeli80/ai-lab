from abc import ABC, abstractmethod


class Provider(ABC):
    """Interfaz común para todos los proveedores de modelos."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre del proveedor."""
        raise NotImplementedError

    @property
    @abstractmethod
    def required_env(self) -> str:
        """Variable de entorno necesaria para utilizar el proveedor."""
        raise NotImplementedError

    @abstractmethod
    def build_model_name(self, model: str) -> str:
        """Construye el identificador que utilizará LiteLLM."""
        raise NotImplementedError
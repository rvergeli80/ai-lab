from gateway_manager.catalog import CatalogLoader
from gateway_manager.mappers.model_mapper import ModelMapper


class ModelRegistry:
    """Registro de modelos del Gateway."""

    def __init__(self, data: dict):
        self.models = data["models"]
        self.aliases = data.get("aliases", {})

    @classmethod
    def load(cls):
        """Carga el catálogo completo mediante el CatalogLoader."""
        data = CatalogLoader.load()
        return cls(data)

    def get(self, name: str):
        """Obtiene un modelo por nombre o alias."""

        if name in self.aliases:
            name = self.aliases[name]

        data = self.models.get(name)

        if data is None:
            return None

        return ModelMapper.from_dict(name, data)

    def list_enabled(self):
        """Devuelve todos los modelos habilitados."""

        result = {}

        for name, model in self.models.items():
            if model["status"] != "enabled":
                continue

            result[name] = ModelMapper.from_dict(name, model)

        return result

    def find_by_capability(self, capability: str):
        """Busca modelos habilitados que soporten una capability."""

        return {
            name: model
            for name, model in self.list_enabled().items()
            if model.has_capability(capability)
        }

    def find_by_tag(self, tag: str):
        """Busca modelos habilitados por tag."""

        return {
            name: model
            for name, model in self.list_enabled().items()
            if model.has_tag(tag)
        }
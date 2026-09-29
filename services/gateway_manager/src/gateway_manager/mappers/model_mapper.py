from gateway_manager.domain import Model


class ModelMapper:
    """Transforma datos del catálogo en entidades de dominio."""

    @staticmethod
    def from_dict(name: str, data: dict) -> Model:
        return Model(
            name=name,
            provider=data["provider"],
            provider_model=data["model"],
            status=data["status"],
            capabilities=data["capabilities"],
            context_window=data["context_window"],
            priority=data["priority"],
            tags=data["tags"],
        )
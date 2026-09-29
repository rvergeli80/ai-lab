from pathlib import Path

import yaml

from gateway_manager.providers import PROVIDERS


REQUIRED_ENV = {
    "openrouter": "OPENROUTER_API_KEY",
    "openai": "OPENAI_API_KEY",
}


def find_lab_root(start: Path) -> Path:
    """Busca la raíz del LAB localizando el fichero lab.yaml."""
    current = start.resolve()

    while current != current.parent:
        if (current / "lab.yaml").exists():
            return current
        current = current.parent

    raise RuntimeError("No se encontró la raíz del LAB (lab.yaml)")


ROOT = find_lab_root(Path(__file__))

MODELS_FILE = ROOT / "config/models/models.yaml"
OUTPUT_FILE = ROOT / "services/gateway/config.yaml"


def load_models() -> dict:
    """Carga el catálogo de modelos."""
    with MODELS_FILE.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_models(data: dict) -> None:
    """Valida la estructura del catálogo."""

    if "models" not in data:
        raise RuntimeError(
            "models.yaml debe contener la clave 'models'"
        )

    for name, model in data["models"].items():

        for field in (
            "provider",
            "model",
            "status",
            "capabilities",
            "context_window",
            "priority",
            "tags",
        ):
            if field not in model:
                raise RuntimeError(
                    f"El modelo '{name}' no contiene el campo '{field}'"
                )

        provider = model["provider"]

        if provider not in REQUIRED_ENV:
            raise RuntimeError(
                f"Proveedor no soportado: {provider}"
            )

        if not isinstance(model["capabilities"], list):
            raise RuntimeError(
                f"'{name}': capabilities debe ser una lista"
            )

        if not isinstance(model["tags"], list):
            raise RuntimeError(
                f"'{name}': tags debe ser una lista"
            )

        if not isinstance(model["context_window"], int):
            raise RuntimeError(
                f"'{name}': context_window debe ser un entero"
            )

        if not isinstance(model["priority"], int):
            raise RuntimeError(
                f"'{name}': priority debe ser un entero"
            )

    aliases = data.get("aliases", {})

    for alias, target in aliases.items():

        if target not in data["models"]:
            raise RuntimeError(
                f"Alias '{alias}' apunta a un modelo inexistente: {target}"
            )


def build_config(data: dict) -> dict:
    """Genera la configuración de LiteLLM."""

    model_list = []

    #
    # Modelos físicos
    #
    for name, model in data["models"].items():

        if model["status"] != "enabled":
            continue

        provider = PROVIDERS[model["provider"]]

        model_list.append(
            provider.generate(name, model)
        )

    #
    # Alias
    #
    aliases = data.get("aliases", {})

    for alias, target in aliases.items():

        model = data["models"][target]

        if model["status"] != "enabled":
            continue

        provider = PROVIDERS[model["provider"]]

        model_list.append(
            provider.generate(alias, model)
        )

    return {"model_list": model_list}


def write_config(config: dict) -> None:
    """Escribe el fichero config.yaml para LiteLLM."""

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            config,
            f,
            sort_keys=False,
            default_flow_style=False,
        )


def main() -> None:
    models = load_models()

    validate_models(models)

    config = build_config(models)

    write_config(config)

    print(f"Generated: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
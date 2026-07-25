from pathlib import Path
import yaml


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
    """Valida la estructura del catálogo de modelos."""

    if "models" not in data:
        raise RuntimeError("models.yaml debe contener la clave 'models'")

    for name, model in data["models"].items():

        for field in ("provider", "model", "status"):
            if field not in model:
                raise RuntimeError(
                    f"El modelo '{name}' no contiene el campo '{field}'"
                )

        provider = model["provider"]

        if provider not in REQUIRED_ENV:
            raise RuntimeError(
                f"Proveedor no soportado: {provider}"
            )


def build_config(data: dict) -> dict:
    """Genera la configuración de LiteLLM."""

    model_list = []

    for name, model in data["models"].items():

        if model["status"] != "enabled":
            continue

        provider = model["provider"]

        if provider == "openrouter":

            model_list.append(
                {
                    "model_name": name,
                    "litellm_params": {
                        "model": f"openrouter/{model['model']}",
                        "api_key": "os.environ/OPENROUTER_API_KEY",
                    },
                }
            )

        elif provider == "openai":

            model_list.append(
                {
                    "model_name": name,
                    "litellm_params": {
                        "model": model["model"],
                        "api_key": "os.environ/OPENAI_API_KEY",
                    },
                }
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
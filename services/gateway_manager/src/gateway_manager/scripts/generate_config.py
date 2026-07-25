from pathlib import Path
import yaml


def find_lab_root(start: Path) -> Path:
    current = start.resolve()

    while current != current.parent:
        if (current / "lab.yaml").exists():
            return current
        current = current.parent

    raise RuntimeError("No se encontró la raíz del LAB (lab.yaml)")


ROOT = find_lab_root(Path(__file__))

MODELS_FILE = ROOT / "config/models/models.yaml"
OUTPUT_FILE = ROOT / "services/gateway/config.yaml"


def load_models():
    with MODELS_FILE.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_config(data):
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


def main():
    config = build_config(load_models())

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, sort_keys=False)

    print(f"Generated: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

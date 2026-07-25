from pathlib import Path
import yaml


ROOT = Path(__file__).resolve().parents[5]

MODELS_FILE = ROOT / "config/models/models.yaml"


def load_models():
    with open(MODELS_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    models = load_models()

    print("Registered models:\n")

    for name, info in models["models"].items():
        print(
            f"- {name} "
            f"({info['provider']}) "
            f"[{info['status']}]"
        )
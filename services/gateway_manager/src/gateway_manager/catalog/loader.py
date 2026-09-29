from pathlib import Path

import yaml


def find_lab_root(start: Path) -> Path:
    current = start.resolve()

    while current != current.parent:
        if (current / "lab.yaml").exists():
            return current
        current = current.parent

    raise RuntimeError("No se encontró lab.yaml")


ROOT = find_lab_root(Path(__file__))

CATALOG_FILE = ROOT / "config/models/catalog.yaml"
PROVIDERS_DIR = ROOT / "config/models/providers"
ALIASES_FILE = ROOT / "config/models/aliases.yaml"


class CatalogLoader:
    """Carga y fusiona el catálogo completo de modelos."""

    @classmethod
    def load(cls) -> dict:

        with CATALOG_FILE.open("r", encoding="utf-8") as f:
            catalog = yaml.safe_load(f)

        models = {}

        for provider in catalog["providers"]:

            provider_file = PROVIDERS_DIR / f"{provider}.yaml"

            if not provider_file.exists():
                raise FileNotFoundError(provider_file)

            with provider_file.open("r", encoding="utf-8") as f:
                provider_data = yaml.safe_load(f) or {}

            models.update(provider_data.get("models", {}))

        with ALIASES_FILE.open("r", encoding="utf-8") as f:
            aliases = yaml.safe_load(f) or {}

        return {
            "models": models,
            "aliases": aliases.get("aliases", {}),
        }
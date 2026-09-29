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
POLICIES_FILE = ROOT / "config/routing/policies.yaml"


class PolicyLoader:

    @classmethod
    def load(cls) -> dict:
        with POLICIES_FILE.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        if "policies" not in data:
            raise RuntimeError(
                "policies.yaml debe contener la clave 'policies'"
            )

        return data

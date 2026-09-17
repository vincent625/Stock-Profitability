from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def model_config(path: str | Path) -> dict[str, Any]:
    data = load_yaml(path)
    if "model" not in data:
        raise ValueError(f"Missing top-level 'model' key in {path}")
    return data["model"]

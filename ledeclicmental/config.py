"""Central configuration — loaded once from .env at import time."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env", override=False)


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {key}\n"
            f"Copy .env.example to .env and fill in the values."
        )
    return value


@dataclass(frozen=True)
class Settings:
    # Groq
    groq_api_key: str

    # Paths
    project_root: Path
    assets_dir: Path
    data_dir: Path
    post_history_file: Path

    # Behaviour
    log_level: str


def load_settings() -> Settings:
    root = _PROJECT_ROOT
    return Settings(
        groq_api_key=_require("GROQ_API_KEY"),
        project_root=root,
        assets_dir=root / "assets",
        data_dir=root / "data",
        post_history_file=root / os.getenv("POST_HISTORY_FILE", "data/post_history.json"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


# Module-level singleton — import this everywhere
settings = load_settings()

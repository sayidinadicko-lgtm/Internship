"""Central configuration — loaded once from .env at import time."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Resolve .env relative to this file's parent (project root)
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


def _parse_post_times(raw: str) -> list[tuple[int, int]]:
    """Parse 'HH:MM,HH:MM,HH:MM' into [(h,m), ...]"""
    result = []
    for entry in raw.split(","):
        entry = entry.strip()
        h, m = entry.split(":")
        result.append((int(h), int(m)))
    return result


@dataclass(frozen=True)
class Settings:
    # Instagram
    instagram_username: str
    instagram_password: str
    instagram_session_file: Path

    # Claude
    anthropic_api_key: str
    claude_model: str

    # Schedule
    post_times: list[tuple[int, int]]
    timezone: str

    # Paths
    project_root: Path
    assets_dir: Path
    data_dir: Path
    post_history_file: Path

    # Behaviour
    dry_run: bool
    log_level: str


def load_settings() -> Settings:
    root = _PROJECT_ROOT
    return Settings(
        instagram_username=_require("INSTAGRAM_USERNAME"),
        instagram_password=_require("INSTAGRAM_PASSWORD"),
        instagram_session_file=root / os.getenv("INSTAGRAM_SESSION_FILE", "data/session/instagram_session.json"),
        anthropic_api_key=_require("ANTHROPIC_API_KEY"),
        claude_model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6"),
        post_times=_parse_post_times(os.getenv("POST_TIMES", "07:00,12:30,19:00")),
        timezone=os.getenv("TIMEZONE", "Europe/Paris"),
        project_root=root,
        assets_dir=root / "assets",
        data_dir=root / "data",
        post_history_file=root / os.getenv("POST_HISTORY_FILE", "data/post_history.json"),
        dry_run=os.getenv("DRY_RUN", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


# Module-level singleton — import this everywhere
settings = load_settings()

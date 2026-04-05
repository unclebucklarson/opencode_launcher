# Copyright (c) 2026 csb (unclebucklarson)
# Licensed under the MIT License - see LICENSE file for details

"""Configuration management for OpenCode Launcher."""

import base64
import json
import logging
import os
import re
from pathlib import Path

from .constants import (
    CONFIG_DIR,
    AGENTS_DIR,
    DEFAULT_CONFIG_FILE,
    PRESETS_DIR,
    ENV_FILE,
)

log = logging.getLogger(__name__)

CONFIG_SCHEMA = {
    "model": str,
    "model_type": lambda v: v in ("local", "cloud"),
    "directory": str,
    "agent": str,
    "terminal": str,
}


def _load_env_file():
    """Load environment variables from .env file in config directory."""
    if not ENV_FILE.exists():
        return
    try:
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            if key:
                os.environ.setdefault(key, value)
    except IOError as e:
        log.warning("Failed to load .env file: %s", e)


_load_env_file()


def ensure_dirs():
    """Create config directory structure if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    PRESETS_DIR.mkdir(parents=True, exist_ok=True)


def load_config(path: str | None = None) -> dict | None:
    """Load a JSON config file. Returns None if not found."""
    config_path = Path(path) if path else DEFAULT_CONFIG_FILE
    config_path = config_path.expanduser().resolve()
    if not config_path.exists():
        log.debug("Config file not found: %s", config_path)
        return None
    try:
        with open(config_path) as f:
            data = json.load(f)
        log.info("Loaded config from %s", config_path)
        return data
    except (json.JSONDecodeError, IOError) as e:
        log.error("Failed to load config %s: %s", config_path, e)
        return None


def save_config(data: dict, path: str | None = None):
    """Save config data to JSON file."""
    config_path = Path(path) if path else DEFAULT_CONFIG_FILE
    config_path = config_path.expanduser().resolve()
    ensure_dirs()
    with open(config_path, "w") as f:
        json.dump(data, f, indent=2)
    log.info("Saved config to %s", config_path)


def validate_config(data: dict) -> list[str]:
    """Validate config data, return list of error messages."""
    errors = []
    if "model_type" in data and data["model_type"] not in ("local", "cloud"):
        errors.append(
            f"model_type: must be 'local' or 'cloud', got '{data['model_type']}'"
        )
    if "directory" in data:
        d = Path(data["directory"]).expanduser()
        if not d.exists():
            errors.append(f"directory: path does not exist: {d}")
    if "agent" in data:
        agent_file = AGENTS_DIR / f"{data['agent']}.md"
        if not agent_file.exists():
            errors.append(f"agent: template not found: {agent_file}")
    for key in data:
        if key not in CONFIG_SCHEMA:
            errors.append(f"unknown field: '{key}'")
    return errors


def list_presets() -> list[dict]:
    """List all saved config presets."""
    ensure_dirs()
    presets = []
    for f in sorted(PRESETS_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text())
            presets.append(
                {
                    "name": f.stem,
                    "file": str(f),
                    "model": data.get("model", "?"),
                    "model_type": data.get("model_type", "?"),
                    "directory": data.get("directory", "?"),
                    "agent": data.get("agent", "?"),
                }
            )
        except (json.JSONDecodeError, IOError):
            continue
    return presets


def save_preset(name: str, data: dict) -> bool:
    """Save a config preset. Returns True on success."""
    ensure_dirs()
    name = re.sub(r"[^a-zA-Z0-9_-]", "-", name).lower()
    if not name:
        return False
    path = PRESETS_DIR / f"{name}.json"
    try:
        path.write_text(json.dumps(data, indent=2))
        return True
    except IOError:
        return False


def load_preset(name: str) -> dict | None:
    """Load a config preset by name."""
    path = PRESETS_DIR / f"{name}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, IOError):
        return None


def delete_preset(name: str) -> bool:
    """Delete a config preset."""
    path = PRESETS_DIR / f"{name}.json"
    if path.exists():
        path.unlink()
        return True
    return False


def export_config(data: dict) -> str:
    """Export config as base64 string for sharing."""
    return base64.b64encode(json.dumps(data).encode()).decode()


def import_config(encoded: str) -> dict | None:
    """Import config from base64 string."""
    try:
        return json.loads(base64.b64decode(encoded).decode())
    except Exception:
        return None

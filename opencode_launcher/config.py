# Copyright (c) 2026 csb (unclebucklarson)
# Licensed under the MIT License - see LICENSE file for details

"""Configuration management for OpenCode Launcher."""

import json
import logging
from pathlib import Path
from typing import Optional

from .constants import CONFIG_DIR, AGENTS_DIR, DEFAULT_CONFIG_FILE

log = logging.getLogger(__name__)


def ensure_dirs():
    """Create config directory structure if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)


def load_config(path: Optional[str] = None) -> Optional[dict]:
    """Load a JSON config file. Returns None if not found, empty dict if file is empty."""
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


def save_config(data: dict, path: Optional[str] = None):
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
    if "directory" in data:
        d = Path(data["directory"]).expanduser()
        if not d.exists():
            errors.append(f"Directory does not exist: {d}")
    if "agent" in data:
        agent_file = AGENTS_DIR / f"{data['agent']}.md"
        if not agent_file.exists():
            errors.append(f"Agent template not found: {agent_file}")
    return errors

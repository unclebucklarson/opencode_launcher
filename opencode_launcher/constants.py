# Copyright (c) 2026 csb (unclebucklarson)
# Licensed under the MIT License - see LICENSE file for details

"""Constants and paths for OpenCode Launcher."""

import os
from pathlib import Path

APP_NAME = "opencode-launcher"
CONFIG_DIR = Path(os.environ.get("OC_CONFIG_DIR", Path.home() / ".config" / APP_NAME))
AGENTS_DIR = CONFIG_DIR / "agents"
SESSIONS_FILE = CONFIG_DIR / "sessions.json"
INSTANCES_FILE = CONFIG_DIR / "instances.json"
STOPPED_INSTANCES_FILE = CONFIG_DIR / "stopped_instances.json"
DEFAULT_CONFIG_FILE = CONFIG_DIR / "config.json"
PRESETS_DIR = CONFIG_DIR / "presets"
LOGS_DIR = CONFIG_DIR / "logs"
ENV_FILE = CONFIG_DIR / ".env"

OPENCODE_AUTH_FILE = Path.home() / ".local" / "share" / "opencode" / "auth.json"

OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
OLLAMA_TAGS_ENDPOINT = f"{OLLAMA_API_URL}/api/tags"
OLLAMA_PULL_ENDPOINT = f"{OLLAMA_API_URL}/api/pull"
OLLAMA_DELETE_ENDPOINT = f"{OLLAMA_API_URL}/api/delete"
OLLAMA_SHOW_ENDPOINT = f"{OLLAMA_API_URL}/api/show"
OLLAMA_PS_ENDPOINT = f"{OLLAMA_API_URL}/api/ps"

ZEN_MODELS_URL = "https://opencode.ai/zen/v1/models"

MAX_SESSIONS = 10
OLLAMA_MAX_RETRIES = 3
OLLAMA_RETRY_BACKOFF = 2.0

TERMINAL_PREFERENCES = ["gnome-terminal", "konsole", "kitty", "xterm"]

BANNER = r"""
  ___                    ____          _
 / _ \ _ __   ___ _ __  / ___|___   __| | ___
| | | | '_ \ / _ \ '_ \| |   / _ \ / _` |/ _ \
| |_| | |_) |  __/ | | | |__| (_) | (_| |  __/
 \___/| .__/ \___|_| |_|\____\___/ \__,_|\___|
      |_|               Launcher
"""

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
DEFAULT_CONFIG_FILE = CONFIG_DIR / "config.json"

OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
OLLAMA_TAGS_ENDPOINT = f"{OLLAMA_API_URL}/api/tags"

MAX_SESSIONS = 10

TERMINAL_PREFERENCES = ["terminator", "gnome-terminal", "konsole", "xterm"]

BANNER = r"""
  ___                    ____          _
 / _ \ _ __   ___ _ __  / ___|___   __| | ___
| | | | '_ \ / _ \ '_ \| |   / _ \ / _` |/ _ \
| |_| | |_) |  __/ | | | |__| (_) | (_| |  __/
 \___/| .__/ \___|_| |_|\____\___/ \__,_|\___|
      |_|               Launcher
"""

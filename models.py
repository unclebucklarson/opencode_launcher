# Copyright (c) 2026 csb (unclebucklarson)
# Licensed under the MIT License - see LICENSE file for details

"""Model selection and Ollama integration."""
import json
import logging
import urllib.request
import urllib.error
from typing import Optional

from .constants import OLLAMA_TAGS_ENDPOINT

log = logging.getLogger(__name__)


def is_ollama_running() -> bool:
    """Check if Ollama API is reachable."""
    try:
        req = urllib.request.Request(OLLAMA_TAGS_ENDPOINT, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError):
        return False


def get_ollama_models() -> list[str]:
    """Query Ollama API and return list of available model names."""
    try:
        req = urllib.request.Request(OLLAMA_TAGS_ENDPOINT, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        models = [m["name"] for m in data.get("models", [])]
        models.sort()
        return models
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError) as e:
        log.error("Failed to query Ollama models: %s", e)
        return []


def validate_local_model_constraint(requested_model: str, running_models: list[str]) -> Optional[str]:
    """
    Enforce: all local instances must use the same model.
    Returns error message if constraint violated, None if OK.
    """
    if not running_models:
        return None
    unique = set(running_models)
    if len(unique) == 1 and requested_model in unique:
        return None
    if len(unique) == 1:
        current = unique.pop()
        return (
            f"All local instances must use the same model. "
            f"Currently running: '{current}'. "
            f"Requested: '{requested_model}'. "
            f"Stop existing instances first, or use '{current}'."
        )
    # Multiple models already running (shouldn't happen)
    return (
        f"Multiple local models detected ({', '.join(unique)}). "
        f"Please kill-all and start fresh."
    )

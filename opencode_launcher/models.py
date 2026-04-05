# Copyright (c) 2026 csb (unclebucklarson)
# Licensed under the MIT License - see LICENSE file for details

"""Model selection and Ollama integration."""

import json
import logging
import time
import urllib.request
import urllib.error
from typing import Optional

from .constants import (
    OLLAMA_TAGS_ENDPOINT,
    OLLAMA_PULL_ENDPOINT,
    OLLAMA_DELETE_ENDPOINT,
    OLLAMA_SHOW_ENDPOINT,
    OLLAMA_PS_ENDPOINT,
    OLLAMA_MAX_RETRIES,
    OLLAMA_RETRY_BACKOFF,
    ZEN_MODELS_URL,
)

log = logging.getLogger(__name__)


def _ollama_request(
    url: str, method: str = "GET", data: dict | None = None, timeout: int = 10
) -> dict | None:
    """Make an Ollama API request with retry logic.

    Returns parsed JSON dict on success, None on failure.
    """
    last_error = None
    for attempt in range(OLLAMA_MAX_RETRIES):
        try:
            body = json.dumps(data).encode() if data else None
            req = urllib.request.Request(url, data=body, method=method)
            if body:
                req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    raw = resp.read().decode()
                    return json.loads(raw) if raw else {}
        except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError) as e:
            last_error = e
            if attempt < OLLAMA_MAX_RETRIES - 1:
                wait = OLLAMA_RETRY_BACKOFF * (2**attempt)
                log.debug(
                    "Ollama request failed (attempt %d/%d), retrying in %.1fs: %s",
                    attempt + 1,
                    OLLAMA_MAX_RETRIES,
                    wait,
                    e,
                )
                time.sleep(wait)
    log.error(
        "Ollama request failed after %d attempts: %s", OLLAMA_MAX_RETRIES, last_error
    )
    return None


def is_ollama_running() -> bool:
    """Check if Ollama API is reachable."""
    result = _ollama_request(OLLAMA_TAGS_ENDPOINT, timeout=5)
    return result is not None


def get_ollama_models() -> list[str]:
    """Query Ollama API and return list of available model names."""
    result = _ollama_request(OLLAMA_TAGS_ENDPOINT)
    if result is None:
        return []
    models = [m["name"] for m in result.get("models", [])]
    models.sort()
    return models


def get_ollama_running_models() -> list[str]:
    """Query Ollama API and return list of currently loaded/running model names."""
    result = _ollama_request(OLLAMA_PS_ENDPOINT, timeout=5)
    if result is None:
        return []
    models = [m["name"] for m in result.get("models", [])]
    return models


def pull_ollama_model(model: str, timeout: int = 300) -> bool:
    """Pull a model from Ollama. Returns True on success."""
    result = _ollama_request(
        OLLAMA_PULL_ENDPOINT,
        method="POST",
        data={"model": model, "stream": False},
        timeout=timeout,
    )
    if result is None:
        return False
    return "status" in result


def remove_ollama_model(model: str) -> bool:
    """Remove a local Ollama model. Returns True on success."""
    result = _ollama_request(
        OLLAMA_DELETE_ENDPOINT, method="DELETE", data={"model": model}
    )
    return result is not None


def get_ollama_model_info(model: str) -> dict | None:
    """Get details about a specific Ollama model."""
    return _ollama_request(
        OLLAMA_SHOW_ENDPOINT, method="POST", data={"model": model, "verbose": False}
    )


def validate_local_model_constraint(
    requested_model: str, running_models: list[str]
) -> Optional[str]:
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
    return (
        f"Multiple local models detected ({', '.join(unique)}). "
        f"Please kill-all and start fresh."
    )


def get_zen_models() -> list[str]:
    """Fetch available models from OpenCode Zen API."""
    try:
        req = urllib.request.Request(
            ZEN_MODELS_URL, headers={"User-Agent": "opencode-launcher/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                models = [m["id"] for m in data.get("data", [])]
                models.sort()
                return models
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError) as e:
        log.error("Failed to fetch Zen models: %s", e)
    return []

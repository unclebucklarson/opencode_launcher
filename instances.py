"""Instance tracking - manage running OpenCode instances."""
import json
import logging
import os
import signal
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .constants import INSTANCES_FILE, CONFIG_DIR

log = logging.getLogger(__name__)


def _ensure_file():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not INSTANCES_FILE.exists():
        INSTANCES_FILE.write_text("{}")


def _load() -> dict:
    _ensure_file()
    try:
        with open(INSTANCES_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save(data: dict):
    _ensure_file()
    with open(INSTANCES_FILE, "w") as f:
        json.dump(data, f, indent=2)


def is_pid_alive(pid: int) -> bool:
    """Check if a process with given PID is still running."""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def cleanup_stale():
    """Remove instances whose PIDs are no longer running."""
    data = _load()
    stale = [iid for iid, info in data.items() if not is_pid_alive(info.get("pid", -1))]
    for iid in stale:
        log.info("Cleaning stale instance: %s (PID %s)", iid, data[iid].get("pid"))
        del data[iid]
    if stale:
        _save(data)
    return len(stale)


def add_instance(
    pid: int,
    model: str,
    directory: str,
    agent: str,
    terminal: str,
    model_type: str = "local",
) -> str:
    """Register a new running instance. Returns instance ID."""
    data = _load()
    instance_id = str(uuid.uuid4())[:8]
    data[instance_id] = {
        "pid": pid,
        "model": model,
        "model_type": model_type,
        "directory": directory,
        "agent": agent,
        "terminal": terminal,
        "start_time": datetime.now(timezone.utc).isoformat(),
    }
    _save(data)
    return instance_id


def remove_instance(instance_id: str) -> bool:
    """Remove an instance from tracking."""
    data = _load()
    if instance_id in data:
        del data[instance_id]
        _save(data)
        return True
    return False


def stop_instance(instance_id: str) -> tuple[bool, str]:
    """Stop a specific instance by ID. Returns (success, message)."""
    data = _load()
    if instance_id not in data:
        return False, f"Instance '{instance_id}' not found."
    info = data[instance_id]
    pid = info.get("pid", -1)
    if not is_pid_alive(pid):
        del data[instance_id]
        _save(data)
        return True, f"Instance '{instance_id}' was already stopped (stale). Cleaned up."
    try:
        os.kill(pid, signal.SIGTERM)
        del data[instance_id]
        _save(data)
        return True, f"Instance '{instance_id}' (PID {pid}) terminated."
    except OSError as e:
        return False, f"Failed to stop PID {pid}: {e}"


def kill_all() -> list[str]:
    """Kill all tracked instances. Returns list of messages."""
    data = _load()
    messages = []
    for iid, info in list(data.items()):
        pid = info.get("pid", -1)
        if is_pid_alive(pid):
            try:
                os.kill(pid, signal.SIGTERM)
                messages.append(f"Killed '{iid}' (PID {pid})")
            except OSError as e:
                messages.append(f"Failed to kill '{iid}' (PID {pid}): {e}")
        else:
            messages.append(f"Cleaned stale '{iid}' (PID {pid})")
    _save({})
    return messages


def get_instances() -> dict:
    """Get all tracked instances (after cleanup)."""
    cleanup_stale()
    return _load()


def get_running_local_models() -> list[str]:
    """Get list of models used by currently running local instances."""
    instances = get_instances()
    return [
        info["model"]
        for info in instances.values()
        if info.get("model_type") == "local"
    ]


def format_instance(instance_id: str, info: dict) -> str:
    """Format an instance for display."""
    pid = info.get("pid", "?")
    model = info.get("model", "?")
    model_type = info.get("model_type", "local")
    directory = info.get("directory", "?")
    agent = info.get("agent", "?")
    terminal = info.get("terminal", "?")
    start = info.get("start_time", "?")
    alive = "🟢 running" if is_pid_alive(pid) else "🔴 stopped"
    try:
        dt = datetime.fromisoformat(start)
        start_str = dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        start_str = start
    return (
        f"  {instance_id} | {alive} | PID {pid}\n"
        f"    Model: {model_type}:{model} | Agent: {agent}\n"
        f"    Dir:   {directory}\n"
        f"    Term:  {terminal} | Started: {start_str}"
    )

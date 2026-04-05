# Copyright (c) 2026 csb (unclebucklarson)
# Licensed under the MIT License - see LICENSE file for details

"""Instance tracking - manage running OpenCode instances."""

import fcntl
import json
import logging
import os
import signal
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .constants import INSTANCES_FILE, CONFIG_DIR, STOPPED_INSTANCES_FILE

log = logging.getLogger(__name__)


def _ensure_file():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not INSTANCES_FILE.exists():
        INSTANCES_FILE.write_text("{}")
    if not STOPPED_INSTANCES_FILE.exists():
        STOPPED_INSTANCES_FILE.write_text("{}")


def _load_stopped() -> dict:
    _ensure_file()
    try:
        with open(STOPPED_INSTANCES_FILE) as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                return json.load(f)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_stopped(data: dict):
    _ensure_file()
    with open(STOPPED_INSTANCES_FILE, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            json.dump(data, f, indent=2)
            f.flush()
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def _load() -> dict:
    _ensure_file()
    try:
        with open(INSTANCES_FILE) as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                return json.load(f)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except (json.JSONDecodeError, IOError):
        return {}


def _save(data: dict):
    _ensure_file()
    with open(INSTANCES_FILE, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            json.dump(data, f, indent=2)
            f.flush()
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def is_pid_alive(pid: int) -> bool:
    """Check if a process with given PID is still running."""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def is_pid_alive_and_same(pid: int, start_time: str | None = None) -> bool:
    """Check if PID is alive and (optionally) started after the given time.

    This helps detect PID reuse: if the process at this PID started before
    our recorded start_time, it's a different process.
    """
    if not is_pid_alive(pid):
        return False
    if start_time is None:
        return True
    try:
        dt = datetime.fromisoformat(start_time)
        proc_boot = datetime.fromtimestamp(
            os.path.getmtime(f"/proc/{pid}"), tz=timezone.utc
        )
        # If the process inode/boot is older than our record, it's a reused PID
        return proc_boot >= dt
    except (OSError, ValueError):
        # Can't verify — assume alive
        return True


def cleanup_stale():
    """Remove instances whose PIDs are no longer running."""
    data = _load()
    stale = [
        iid
        for iid, info in data.items()
        if not is_pid_alive_and_same(info.get("pid", -1), info.get("start_time"))
    ]
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
    if not is_pid_alive_and_same(pid, info.get("start_time")):
        del data[instance_id]
        _save(data)
        return (
            True,
            f"Instance '{instance_id}' was already stopped (stale). Cleaned up.",
        )
    try:
        os.kill(pid, signal.SIGTERM)
        # Save to stopped instances for potential restart
        stopped = _load_stopped()
        stopped[instance_id] = info
        _save_stopped(stopped)
        del data[instance_id]
        _save(data)
        return True, f"Instance '{instance_id}' (PID {pid}) terminated."
    except OSError as e:
        return False, f"Failed to stop PID {pid}: {e}"


def get_stopped_instances() -> dict:
    """Get all stopped instances available for restart."""
    return _load_stopped()


def restart_instance(instance_id: str) -> dict | None:
    """Get a stopped instance's config for restart. Returns config dict or None."""
    stopped = _load_stopped()
    if instance_id not in stopped:
        return None
    info = stopped[instance_id]
    del stopped[instance_id]
    _save_stopped(stopped)
    return info


def remove_stopped_instance(instance_id: str) -> bool:
    """Remove a stopped instance from the restart list."""
    stopped = _load_stopped()
    if instance_id in stopped:
        del stopped[instance_id]
        _save_stopped(stopped)
        return True
    return False


def kill_all() -> list[str]:
    """Kill all tracked instances. Returns list of messages."""
    data = _load()
    messages = []
    for iid, info in list(data.items()):
        pid = info.get("pid", -1)
        if is_pid_alive_and_same(pid, info.get("start_time")):
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
    alive = (
        "🟢 running"
        if is_pid_alive_and_same(pid, info.get("start_time"))
        else "🔴 stopped"
    )
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

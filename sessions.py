"""Session management - track last N sessions for resume."""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .constants import SESSIONS_FILE, MAX_SESSIONS, CONFIG_DIR

log = logging.getLogger(__name__)


def _ensure_file():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not SESSIONS_FILE.exists():
        SESSIONS_FILE.write_text("[]")


def load_sessions() -> list[dict]:
    """Load session history."""
    _ensure_file()
    try:
        with open(SESSIONS_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_sessions(sessions: list[dict]):
    """Save session history (keeps last MAX_SESSIONS)."""
    _ensure_file()
    trimmed = sessions[-MAX_SESSIONS:]
    with open(SESSIONS_FILE, "w") as f:
        json.dump(trimmed, f, indent=2)


def add_session(model: str, directory: str, agent: str, terminal: str, model_type: str = "local"):
    """Record a new session."""
    sessions = load_sessions()
    session = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "model_type": model_type,
        "directory": directory,
        "agent": agent,
        "terminal": terminal,
    }
    sessions.append(session)
    save_sessions(sessions)
    log.info("Session recorded: %s", session)


def get_sessions() -> list[dict]:
    """Return sessions sorted newest first."""
    sessions = load_sessions()
    sessions.reverse()
    return sessions


def format_session(session: dict, index: int) -> str:
    """Format a session for display."""
    ts = session.get("timestamp", "unknown")
    try:
        dt = datetime.fromisoformat(ts)
        ts_str = dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        ts_str = ts
    model = session.get("model", "?")
    directory = session.get("directory", "?")
    agent = session.get("agent", "?")
    model_type = session.get("model_type", "local")
    return f"[{index}] {ts_str} | {model_type}:{model} | {agent} | {directory}"

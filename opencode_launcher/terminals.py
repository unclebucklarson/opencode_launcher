# Copyright (c) 2026 csb (unclebucklarson)
# Licensed under the MIT License - see LICENSE file for details

"""Terminal detection and launching."""

import logging
import shutil
import subprocess
from pathlib import Path

from .constants import TERMINAL_PREFERENCES

log = logging.getLogger(__name__)


def detect_terminals() -> list[str]:
    """Detect available terminal emulators on the system."""
    available = []
    for term in TERMINAL_PREFERENCES:
        if shutil.which(term):
            available.append(term)
    return available


def get_preferred_terminal(available: list[str]) -> str | None:
    """Return the preferred terminal from available list."""
    if not available:
        return None
    # Follow preference order
    for pref in TERMINAL_PREFERENCES:
        if pref in available:
            return pref
    return available[0]


def build_launch_command(
    terminal: str,
    title: str,
    working_dir: str,
    opencode_cmd: str,
) -> list[str]:
    """Build the command to launch OpenCode in a new terminal window."""
    wd = str(Path(working_dir).expanduser().resolve())

    if terminal == "terminator":
        return [
            "terminator",
            "--new-tab",
            "-T",
            title,
            "-x",
            "bash",
            "-c",
            f"cd '{wd}' && {opencode_cmd}; exec bash",
        ]
    elif terminal == "gnome-terminal":
        return [
            "gnome-terminal",
            "--title",
            title,
            "--working-directory",
            wd,
            "--",
            "bash",
            "-c",
            f"{opencode_cmd}; exec bash",
        ]
    elif terminal == "konsole":
        return [
            "konsole",
            "--workdir",
            wd,
            "-p",
            f"tabtitle={title}",
            "-e",
            "bash",
            "-c",
            f"{opencode_cmd}; exec bash",
        ]
    elif terminal == "kitty":
        return [
            "kitty",
            "--title",
            title,
            "--directory",
            wd,
            "--",
            "bash",
            "-c",
            f"{opencode_cmd}; exec bash",
        ]
    elif terminal == "xterm":
        return [
            "xterm",
            "-T",
            title,
            "-e",
            "bash",
            "-c",
            f"cd '{wd}' && {opencode_cmd}; exec bash",
        ]
    else:
        return [
            terminal,
            "-e",
            "bash",
            "-c",
            f"cd '{wd}' && {opencode_cmd}; exec bash",
        ]


def launch_in_terminal(
    terminal: str,
    title: str,
    working_dir: str,
    opencode_cmd: str,
) -> int | None:
    """
    Launch a command in a new terminal window.
    Returns the PID of the terminal process, or None on failure.
    Note: Some terminals (terminator) fork and exit immediately, so the returned
    PID may not reflect the actual running session. Instance tracking considers
    this and handles stale PIDs gracefully.
    """
    cmd = build_launch_command(terminal, title, working_dir, opencode_cmd)
    log.info("Launching: %s", " ".join(cmd))
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return proc.pid
    except FileNotFoundError:
        log.error("Terminal '%s' not found in PATH", terminal)
        return None
    except OSError as e:
        log.error("Failed to launch terminal: %s", e)
        return None

#!/usr/bin/env python3

# Copyright (c) 2026 csb (unclebucklarson)
# Licensed under the MIT License - see LICENSE file for details

"""
OpenCode Launcher CLI - Launch and manage OpenCode instances like a pro.

Usage:
    oc launch                          # Interactive mode
    oc launch --config project.json    # From config file
    oc launch --model qwen2.5-coder:32b --dir ~/src/project1 --agent coding
    oc status                          # Show running instances
    oc stop <id>                       # Stop an instance
    oc kill-all                        # Stop everything
    oc resume                          # Resume from session history
    oc resume --new_location ~/new     # Resume settings in new dir
    oc list-agents                     # Show agent templates
    oc list-models                     # Show Ollama models
"""

import argparse
import itertools
import json
import logging
import os
import sys
import threading
import time
from pathlib import Path

from . import __version__
from .constants import BANNER, LOGS_DIR
from .config import (
    load_config,
    validate_config,
    ensure_dirs,
    save_config,
    list_presets,
    save_preset,
    load_preset,
    delete_preset,
    export_config,
    import_config,
)
from .models import (
    is_ollama_running,
    get_ollama_models,
    validate_local_model_constraint,
    pull_ollama_model,
    remove_ollama_model,
    get_ollama_model_info,
)
from .terminals import detect_terminals, get_preferred_terminal, launch_in_terminal
from .sessions import add_session, get_sessions, format_session, clear_sessions
from .instances import (
    add_instance,
    get_instances,
    stop_instance,
    kill_all,
    format_instance,
    get_running_local_models,
    get_stopped_instances,
    restart_instance,
)
from .agents import list_agents, get_agent_slugs, get_agent_path, format_agent

log = logging.getLogger("oc")

# ---------------------------------------------------------------------------
# Colored output helpers
# ---------------------------------------------------------------------------

_HAS_COLORAMA = False
try:
    from colorama import init as colorama_init
    from colorama import Fore as C_Fore
    from colorama import Style as C_Style

    colorama_init(autoreset=True)
    _HAS_COLORAMA = True
except ImportError:
    C_Fore = type("Fore", (), {"GREEN": "", "RED": "", "CYAN": "", "YELLOW": ""})()
    C_Style = type("Style", (), {"RESET_ALL": "", "BRIGHT": ""})()


def _color(color: str, text: str) -> str:
    if _HAS_COLORAMA:
        return f"{color}{text}{C_Style.RESET_ALL}"
    return text


def _green(text: str) -> str:
    return _color(C_Fore.GREEN, text)


def _red(text: str) -> str:
    return _color(C_Fore.RED, text)


def _cyan(text: str) -> str:
    return _color(C_Fore.CYAN, text)


def _yellow(text: str) -> str:
    return _color(C_Fore.YELLOW, text)


def _bold(text: str) -> str:
    if _HAS_COLORAMA:
        return f"{C_Style.BRIGHT}{text}{C_Style.RESET_ALL}"
    return text


# ---------------------------------------------------------------------------
# Spinner / progress indicator
# ---------------------------------------------------------------------------


class Spinner:
    """Simple CLI spinner for long-running operations."""

    def __init__(self, message: str = "Loading..."):
        self.message = message
        self._stop_event = threading.Event()
        self._thread = None

    def _spin(self):
        symbols = itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])
        while not self._stop_event.is_set():
            sys.stdout.write(f"\r{_cyan(next(symbols))} {self.message}")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * (len(self.message) + 2) + "\r")
        sys.stdout.flush()

    def __enter__(self):
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *args):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)


# ---------------------------------------------------------------------------
# TUI helpers (questionary) - graceful fallback to input() if not installed
# ---------------------------------------------------------------------------

_HAS_QUESTIONARY = False
try:
    import questionary
    from questionary import Style

    _Q_STYLE = Style(
        [
            ("qmark", "fg:cyan bold"),
            ("question", "bold"),
            ("answer", "fg:green bold"),
            ("pointer", "fg:cyan bold"),
            ("highlighted", "fg:cyan bold"),
            ("selected", "fg:green"),
        ]
    )
    _HAS_QUESTIONARY = True
except ImportError:
    pass


def _ask_select_filtered(
    message: str,
    choices: list[str],
    default: str | None = None,
    filterable: bool = True,
) -> str:
    """Prompt user to select from a list, with optional typeahead filtering."""
    if _HAS_QUESTIONARY and filterable and len(choices) > 20:
        kwargs = {
            "message": message,
            "choices": choices,
            "style": _Q_STYLE,
        }
        if default is not None and default in choices:
            kwargs["default"] = default
        return questionary.autocomplete(**kwargs).ask() or (sys.exit(0) or "")
    return _ask_select(message, choices, default)


def _ask_select(message: str, choices: list[str], default: str | None = None) -> str:
    """Prompt user to select from a list."""
    if _HAS_QUESTIONARY:
        kwargs = {"message": message, "choices": choices, "style": _Q_STYLE}
        if default is not None and default in choices:
            kwargs["default"] = default
        result = questionary.select(**kwargs).ask()
        if result is None:
            print(f"\n{_red('❌ Aborted.')}")
            sys.exit(0)
        return result
    print(f"\n{message}")
    for i, c in enumerate(choices):
        prefix = "  → " if default and c == default else f"  [{i}] "
        print(f"{prefix}{c}")
    while True:
        try:
            idx = int(input("Enter number: ").strip())
            if 0 <= idx < len(choices):
                return choices[idx]
        except (ValueError, EOFError):
            print(f"\n{_red('❌ Aborted.')}")
            sys.exit(0)
        print("Invalid selection, try again.")


def _ask_text(message: str, default: str = "") -> str:
    """Prompt user for text input."""
    if _HAS_QUESTIONARY:
        result = questionary.text(message, default=default, style=_Q_STYLE).ask()
        if result is None:
            print(f"\n{_red('❌ Aborted.')}")
            sys.exit(0)
        return result
    try:
        result = input(f"{message} [{default}]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print(f"\n{_red('❌ Aborted.')}")
        sys.exit(0)
    return result if result else default


def _ask_confirm(message: str, default: bool = True) -> bool:
    """Prompt user for yes/no."""
    if _HAS_QUESTIONARY:
        result = questionary.confirm(message, default=default, style=_Q_STYLE).ask()
        if result is None:
            print(f"\n{_red('❌ Aborted.')}")
            sys.exit(0)
        return result
    try:
        yn = input(f"{message} [{'Y/n' if default else 'y/N'}]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print(f"\n{_red('❌ Aborted.')}")
        sys.exit(0)
    if not yn:
        return default
    return yn in ("y", "yes")


# ---------------------------------------------------------------------------
# Command implementations
# ---------------------------------------------------------------------------


def cmd_launch(args):
    """Launch a new OpenCode instance."""
    ensure_dirs()

    # --- Load from config file if provided ---
    config_data = {}
    if args.config:
        config_data = load_config(args.config)
        if config_data is None:
            print(f"{_red('❌')} Could not load config: {args.config}")
            return 1
        errors = validate_config(config_data)
        if errors:
            for e in errors:
                print(f"  {_red('❌')} {e}")
            return 1

    # --- Determine model type ---
    model_type = args.model_type or config_data.get("model_type")
    if not model_type:
        model_type = _ask_select(
            "Model source?",
            choices=["local (Ollama)", "cloud (manual entry)"],
            default="local (Ollama)",
        )
        model_type = "local" if "local" in model_type else "cloud"

    # --- Model selection ---
    model = args.model or config_data.get("model")
    if not model:
        if model_type == "local":
            if not is_ollama_running():
                print(
                    f"{_red('❌')} Ollama is not running! Start it with: ollama serve"
                )
                return 1
            with Spinner("Querying Ollama models..."):
                models = get_ollama_models()
            if not models:
                print(
                    f"{_red('❌')} No models found in Ollama. Pull one with: ollama pull <model>"
                )
                return 1
            model = _ask_select_filtered("Select Ollama model:", choices=models)
        else:
            model = _ask_text(
                "Enter cloud model name (e.g., anthropic/claude-3.5-sonnet):"
            )
            if not model:
                print(f"{_red('❌')} Model name is required.")
                return 1

    # --- Enforce local model constraint ---
    if model_type == "local":
        running_models = get_running_local_models()
        constraint_err = validate_local_model_constraint(model, running_models)
        if constraint_err:
            print(f"{_red('❌')} {constraint_err}")
            return 1

    # --- Directory ---
    directory = args.dir or config_data.get("directory")
    if not directory:
        directory = _ask_text("Working directory:", default=str(Path.cwd()))
    directory = str(Path(directory).expanduser().resolve())
    if not Path(directory).exists():
        if _ask_confirm(f"Directory '{directory}' doesn't exist. Create it?"):
            Path(directory).mkdir(parents=True, exist_ok=True)
        else:
            print(f"{_red('❌')} Aborted.")
            return 1

    # --- Agent ---
    agent_slug = args.agent or config_data.get("agent")
    if not agent_slug:
        agents = list_agents()
        if agents:
            choices = [f"{a['slug']:15s} - {a['description']}" for a in agents]
            choices.append("(none) - No agent file")
            selected = _ask_select("Select agent template:", choices=choices)
            if "(none)" not in selected:
                agent_slug = selected.split()[0].strip()
        else:
            print(f"{_yellow('ℹ️')} No agent templates found. Launching without agent.")

    # --- Terminal ---
    terminal = args.terminal or config_data.get("terminal")
    if not terminal:
        available = detect_terminals()
        if not available:
            print(f"{_red('❌')} No supported terminal emulators found!")
            print(
                "   Install one of: terminator, gnome-terminal, konsole, kitty, xterm"
            )
            return 1
        if len(available) == 1:
            terminal = available[0]
            print(f"{_yellow('ℹ️')} Using terminal: {terminal}")
        else:
            preferred = get_preferred_terminal(available)
            terminal = _ask_select(
                "Select terminal emulator:",
                choices=available,
                default=preferred,
            )

    # --- Number of instances ---
    count = args.count or 1
    if count < 1:
        print(f"{_red('❌')} Instance count must be at least 1.")
        return 1

    # --- Dry run mode ---
    if getattr(args, "dry_run", False):
        print(f"\n{_bold('🔍 Dry Run — nothing will be launched')}")
        print(f"   Model:     {model_type}:{model}")
        print(f"   Directory: {directory}")
        print(f"   Agent:     {agent_slug or '(none)'}")
        print(f"   Terminal:  {terminal}")
        print(f"   Instances: {count}")
        print(f"\n{_green('✓')} Configuration is valid. Remove --dry-run to launch.")
        return 0

    # --- Build OpenCode command ---
    oc_cmd_parts = ["opencode"]
    if agent_slug:
        agent_path = get_agent_path(agent_slug)
        if agent_path:
            oc_cmd_parts.extend(["--agent", str(agent_path)])
    if model:
        oc_cmd_parts.extend(["--model", model])
    oc_cmd = " ".join(oc_cmd_parts)

    # For local models, ensure ~/.config/opencode/opencode.json has Ollama provider config
    if model_type == "local" and model:
        opencode_config_dir = Path.home() / ".config" / "opencode"
        opencode_json = opencode_config_dir / "opencode.json"
        ollama_base_url = os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
        # Ensure /v1 suffix for OpenAI-compatible endpoint
        if not ollama_base_url.endswith("/v1"):
            ollama_base_url = ollama_base_url.rstrip("/") + "/v1"

        if not opencode_json.exists():
            ollama_config = {
                "$schema": "https://opencode.ai/config.json",
                "provider": {
                    "ollama": {
                        "npm": "@ai-sdk/openai-compatible",
                        "name": "Ollama (local)",
                        "options": {"baseURL": ollama_base_url},
                        "models": {
                            model: {"name": model},
                        },
                    },
                },
            }
            try:
                opencode_config_dir.mkdir(parents=True, exist_ok=True)
                opencode_json.write_text(json.dumps(ollama_config, indent=2))
                print(f"  ℹ️  Created {opencode_json} with Ollama config")
            except IOError as e:
                print(f"  ⚠️  Could not create opencode.json: {e}")
        else:
            try:
                existing = json.loads(opencode_json.read_text())
                providers = existing.get("provider", {})
                has_ollama = any(
                    "localhost:11434" in str(v.get("options", {}).get("baseURL", ""))
                    for v in providers.values()
                )
                if not has_ollama:
                    print(f"  ⚠️  {opencode_json} exists but no Ollama provider")
            except (json.JSONDecodeError, IOError):
                pass

    print(f"\n{_green('🚀')} Launching {count} instance(s)...")
    print(f"   Model:     {model_type}:{model}")
    print(f"   Directory: {directory}")
    print(f"   Agent:     {agent_slug or '(none)'}")
    print(f"   Terminal:  {terminal}")
    print()

    for i in range(count):
        title = f"OpenCode [{i + 1}/{count}] - {agent_slug or 'default'} @ {Path(directory).name}"
        pid = launch_in_terminal(terminal, title, directory, oc_cmd)
        if pid:
            iid = add_instance(
                pid, model, directory, agent_slug or "", terminal, model_type
            )
            print(f"  {_green('✅')} Instance {iid} started (PID {pid})")
            if terminal == "terminator":
                print(
                    f"    ℹ️  Note: Terminator forks immediately; PID may show as stale. Use 'oc status' to verify."
                )
        else:
            print(f"  {_red('❌')} Failed to launch instance {i + 1}")

    add_session(model, directory, agent_slug or "", terminal, model_type)
    print(f"\n{_green('✨')} Done! Use 'oc status' to check running instances.")
    return 0


def cmd_status(args):
    """Show all running instances."""
    instances = get_instances()
    if not instances:
        print("No running instances. 🍃")
        return 0
    print(f"\n{_bold('📊 Running Instances')} ({len(instances)}):\n")
    for iid, info in instances.items():
        print(format_instance(iid, info))
        print()
    return 0


def cmd_stop(args):
    """Stop a specific instance."""
    if not args.instance_id:
        instances = get_instances()
        if not instances:
            print("No running instances.")
            return 0
        choices = [
            f"{iid} - {info.get('model', '?')} @ {info.get('directory', '?')}"
            for iid, info in instances.items()
        ]
        selected = _ask_select("Select instance to stop:", choices=choices)
        instance_id = selected.split(" - ")[0].strip()
    else:
        instance_id = args.instance_id

    ok, msg = stop_instance(instance_id)
    print(f"{'✅' if ok else '❌'} {msg}")
    return 0 if ok else 1


def cmd_kill_all(args):
    """Kill all running instances."""
    confirmed = _ask_confirm("Kill ALL running instances?", default=False)
    if not confirmed:
        print("Aborted.")
        return 0
    messages = kill_all()
    if not messages:
        print("No instances to kill. 🍃")
    for msg in messages:
        print(f"  🔪 {msg}")
    print("All clear! 🧹")
    return 0


def cmd_resume(args):
    """Resume from session history."""
    sessions = get_sessions()
    if not sessions:
        print("No session history. Launch something first!")
        return 0

    choices = [format_session(s, i) for i, s in enumerate(sessions)]
    selected = _ask_select("Select session to resume:", choices=choices)
    try:
        idx = int(selected.split("]")[0].replace("[", "").strip())
        if idx < 0 or idx >= len(sessions):
            print(f"{_red('❌')} Invalid session selection.")
            return 1
    except (ValueError, IndexError):
        print(f"{_red('❌')} Invalid session selection.")
        return 1
    session = sessions[idx]

    directory = session["directory"]
    if args.new_location:
        directory = str(Path(args.new_location).expanduser().resolve())
        if not Path(directory).exists():
            if _ask_confirm(f"Directory '{directory}' doesn't exist. Create it?"):
                Path(directory).mkdir(parents=True, exist_ok=True)
            else:
                print(f"{_red('❌')} Aborted.")
                return 1
        print(f"{_yellow('ℹ️')} Using new location: {directory}")

    launch_args = argparse.Namespace(
        config=None,
        model_type=session.get("model_type", "local"),
        model=session["model"],
        dir=directory,
        agent=session.get("agent") or None,
        terminal=session.get("terminal") or None,
        count=1,
        dry_run=False,
    )
    return cmd_launch(launch_args)


def cmd_list_agents(args):
    """List available agent templates."""
    agents = list_agents()
    if not agents:
        print("No agent templates found.")
        print(f"Add .md files to: ~/.config/opencode-launcher/agents/")
        return 0
    print(f"\n{_bold('📋 Available Agents')}:\n")
    print(f"  {'SLUG':20s} {'NAME':25s} DESCRIPTION")
    print(f"  {'─' * 20} {'─' * 25} {'─' * 40}")
    for a in agents:
        print(format_agent(a))
        if a.get("warnings"):
            for w in a["warnings"]:
                print(f"    {_yellow('⚠')} {w}")
    print()
    return 0


def cmd_list_models(args):
    """List available Ollama models."""
    if not is_ollama_running():
        print(f"{_red('❌')} Ollama is not running! Start it with: ollama serve")
        return 1
    with Spinner("Querying Ollama models..."):
        models = get_ollama_models()
    if not models:
        print("No models found. Pull one with: ollama pull <model>")
        return 0
    print(f"\n{_bold('🤖 Available Ollama Models')} ({len(models)}):\n")
    for m in models:
        print(f"  • {m}")
    print()
    return 0


def cmd_init(args):
    """Generate a default config interactively."""
    ensure_dirs()
    print(f"\n{_bold('🔧 Config Generator')}")
    print("Answer the prompts to create a config file.\n")

    config = {}

    # Model type
    model_type = _ask_select(
        "Model source?",
        choices=["local (Ollama)", "cloud (manual entry)"],
        default="local (Ollama)",
    )
    config["model_type"] = "local" if "local" in model_type else "cloud"

    # Model
    if config["model_type"] == "local":
        if is_ollama_running():
            with Spinner("Querying Ollama models..."):
                models = get_ollama_models()
            if models:
                config["model"] = _ask_select_filtered(
                    "Select Ollama model:", choices=models
                )
            else:
                config["model"] = _ask_text(
                    "Ollama model name (none found, type manually):"
                )
        else:
            config["model"] = _ask_text(
                "Ollama model name (Ollama not running, type manually):"
            )
    else:
        config["model"] = _ask_text(
            "Enter cloud model name (e.g., anthropic/claude-3.5-sonnet):"
        )

    # Directory
    config["directory"] = _ask_text("Working directory:", default=str(Path.cwd()))

    # Agent
    agents = list_agents()
    if agents:
        choices = [f"{a['slug']:15s} - {a['description']}" for a in agents]
        choices.append("(none) - No agent file")
        selected = _ask_select("Select agent template:", choices=choices)
        if "(none)" not in selected:
            config["agent"] = selected.split()[0].strip()

    # Terminal
    available = detect_terminals()
    if available:
        if len(available) == 1:
            config["terminal"] = available[0]
        else:
            preferred = get_preferred_terminal(available)
            config["terminal"] = _ask_select(
                "Select terminal emulator:",
                choices=available,
                default=preferred,
            )

    # Save
    output = args.output or str(
        Path.home() / ".config" / "opencode-launcher" / "config.json"
    )
    output_path = Path(output).expanduser().resolve()

    if _ask_confirm(f"Save config to {output_path}?", default=True):
        save_config(config, str(output_path))
        print(f"\n{_green('✅')} Config saved to {output_path}")
        print(f"\nUse it with: oc launch --config {output_path}")
    else:
        print(f"\n{_yellow('ℹ️')} Config not saved. Here's what it would look like:")
        import json

        print(json.dumps(config, indent=2))
    return 0


def cmd_restart(args):
    """Restart a stopped instance."""
    stopped = get_stopped_instances()
    if not stopped:
        print("No stopped instances available for restart.")
        return 0

    if args.instance_id:
        instance_id = args.instance_id
    else:
        choices = [
            f"{iid} - {info.get('model', '?')} @ {info.get('directory', '?')}"
            for iid, info in stopped.items()
        ]
        selected = _ask_select("Select instance to restart:", choices=choices)
        instance_id = selected.split(" - ")[0].strip()

    config = restart_instance(instance_id)
    if config is None:
        print(f"{_red('❌')} Instance '{instance_id}' not found in stopped list.")
        return 1

    print(f"{_green('🔄')} Restarting instance {instance_id}...")
    print(
        f"   Model:     {config.get('model_type', 'local')}:{config.get('model', '?')}"
    )
    print(f"   Directory: {config.get('directory', '?')}")
    print(f"   Agent:     {config.get('agent', '(none)')}")
    print(f"   Terminal:  {config.get('terminal', '?')}")

    model = config.get("model", "")
    model_type = config.get("model_type", "local")
    directory = config.get("directory", "")
    agent_slug = config.get("agent", "")
    terminal = config.get("terminal", "")

    oc_cmd_parts = ["opencode"]
    if agent_slug:
        agent_path = get_agent_path(agent_slug)
        if agent_path:
            oc_cmd_parts.extend(["--agent", str(agent_path)])
    if model:
        oc_cmd_parts.extend(["--model", model])
    oc_cmd = " ".join(oc_cmd_parts)

    title = f"OpenCode [restart] - {agent_slug or 'default'} @ {Path(directory).name}"
    pid = launch_in_terminal(terminal, title, directory, oc_cmd)
    if pid:
        iid = add_instance(pid, model, directory, agent_slug, terminal, model_type)
        print(f"\n{_green('✅')} Instance {iid} restarted (PID {pid})")
    else:
        print(f"\n{_red('❌')} Failed to restart instance")
        return 1
    return 0


def cmd_logs(args):
    """View instance logs."""
    instances = get_instances()
    if not instances:
        print("No running instances.")
        return 0

    if args.instance_id:
        instance_id = args.instance_id
    else:
        choices = [
            f"{iid} - {info.get('model', '?')} @ {info.get('directory', '?')}"
            for iid, info in instances.items()
        ]
        selected = _ask_select("Select instance:", choices=choices)
        instance_id = selected.split(" - ")[0].strip()

    if instance_id not in instances:
        print(f"{_red('❌')} Instance '{instance_id}' not found.")
        return 1

    info = instances[instance_id]
    pid = info.get("pid")
    log_file = LOGS_DIR / f"{instance_id}.log"

    if not log_file.exists():
        print(f"{_yellow('ℹ️')} No log file found for instance {instance_id}.")
        print(f"   Logs are captured from next launch onward.")
        return 0

    lines = args.lines or 50
    try:
        content = log_file.read_text()
        all_lines = content.splitlines()
        display = all_lines[-lines:]
        print(
            f"\n{_bold('📜 Logs for instance')} {instance_id} (last {lines} lines):\n"
        )
        for line in display:
            print(line)
        print()
    except IOError as e:
        print(f"{_red('❌')} Failed to read log file: {e}")
        return 1
    return 0


def cmd_config_save(args):
    """Save current settings as a config preset."""
    ensure_dirs()

    if args.list:
        presets = list_presets()
        if not presets:
            print("No saved presets.")
            return 0
        print(f"\n{_bold('📋 Saved Presets')}:\n")
        print(f"  {'NAME':20s} {'MODEL':30s} TYPE      DIRECTORY")
        print(f"  {'─' * 20} {'─' * 30} {'─' * 9} {'─' * 30}")
        for p in presets:
            print(
                f"  {p['name']:20s} {p['model']:30s} {p['model_type']:<9s} {p['directory']}"
            )
        print()
        return 0

    if args.export:
        presets = list_presets()
        if not presets:
            print("No presets to export.")
            return 0
        data = {
            p["name"]: load_preset(p["name"]) for p in presets if load_preset(p["name"])
        }
        encoded = export_config(data)
        print(f"\n{_bold('📦 Exported presets')} (base64):\n")
        print(encoded)
        print()
        return 0

    # Build config from args
    config = {}
    if args.model:
        config["model"] = args.model
    if args.model_type:
        config["model_type"] = args.model_type
    if args.dir:
        config["directory"] = args.dir
    if args.agent:
        config["agent"] = args.agent
    if args.terminal:
        config["terminal"] = args.terminal

    if not config:
        # Load from default config if exists
        default = load_config()
        if default:
            config = default
        else:
            print(f"{_red('❌')} No settings provided and no default config found.")
            print(
                "   Provide flags or run 'oc launch' first to create a default config."
            )
            return 1

    if not args.name:
        args.name = _ask_text("Preset name:")

    if save_preset(args.name, config):
        print(f"{_green('✅')} Preset '{args.name}' saved.")
    else:
        print(f"{_red('❌')} Failed to save preset.")
        return 1
    return 0


def cmd_config_load(args):
    """Load a config preset."""
    if args.list:
        presets = list_presets()
        if not presets:
            print("No saved presets.")
            return 0
        print(f"\n{_bold('📋 Saved Presets')}:\n")
        print(f"  {'NAME':20s} {'MODEL':30s} TYPE      DIRECTORY")
        print(f"  {'─' * 20} {'─' * 30} {'─' * 9} {'─' * 30}")
        for p in presets:
            print(
                f"  {p['name']:20s} {p['model']:30s} {p['model_type']:<9s} {p['directory']}"
            )
        print()
        return 0

    if args.delete:
        if delete_preset(args.name):
            print(f"{_green('✅')} Preset '{args.name}' deleted.")
        else:
            print(f"{_red('❌')} Preset '{args.name}' not found.")
            return 1
        return 0

    if args.import_data:
        data = import_config(args.import_data)
        if data is None:
            print(f"{_red('❌')} Invalid base64 data.")
            return 1
        if isinstance(data, dict):
            for name, preset_data in data.items():
                save_preset(name, preset_data)
            print(f"{_green('✅')} Imported {len(data)} preset(s).")
        return 0

    config = load_preset(args.name)
    if config is None:
        print(f"{_red('❌')} Preset '{args.name}' not found.")
        return 1

    # Apply overrides
    if args.override:
        for pair in args.override:
            if "=" in pair:
                key, _, value = pair.partition("=")
                config[key.strip()] = value.strip()

    # Validate
    errors = validate_config(config)
    if errors:
        for e in errors:
            print(f"  {_red('❌')} {e}")
        return 1

    # Launch with preset config
    launch_args = argparse.Namespace(
        config=None,
        model_type=config.get("model_type"),
        model=config.get("model"),
        dir=config.get("directory"),
        agent=config.get("agent"),
        terminal=config.get("terminal"),
        count=1,
        dry_run=False,
    )
    print(f"{_green('🚀')} Loading preset '{args.name}'...")
    return cmd_launch(launch_args)


def cmd_sessions(args):
    """Manage session history."""
    if args.clear:
        if _ask_confirm("Clear all session history?", default=False):
            clear_sessions()
            print(f"{_green('✅')} Session history cleared.")
        return 0

    if args.export:
        sessions = get_sessions()
        if not sessions:
            print("No sessions to export.")
            return 0
        import json

        Path(args.export).expanduser().resolve().write_text(
            json.dumps(sessions, indent=2)
        )
        print(f"{_green('✅')} Exported {len(sessions)} session(s) to {args.export}")
        return 0

    if args.import_file:
        import json

        try:
            data = json.loads(Path(args.import_file).read_text())
            if isinstance(data, list):
                for s in data:
                    add_session(
                        s.get("model", ""),
                        s.get("directory", ""),
                        s.get("agent", ""),
                        s.get("terminal", ""),
                        s.get("model_type", "local"),
                    )
                print(f"{_green('✅')} Imported {len(data)} session(s).")
            else:
                print(f"{_red('❌')} Invalid session data.")
                return 1
        except (IOError, json.JSONDecodeError) as e:
            print(f"{_red('❌')} Failed to import: {e}")
            return 1
        return 0

    sessions = get_sessions()
    if not sessions:
        print("No session history.")
        return 0
    print(f"\n{_bold('📜 Session History')}:\n")
    for i, s in enumerate(sessions):
        print(format_session(s, i))
    print()
    return 0


def cmd_ollama(args):
    """Manage Ollama models."""
    if not args.subcommand:
        print("Usage: oc ollama {list|pull|rm|info}")
        return 1

    if args.subcommand == "list":
        return cmd_list_models(args)

    if args.subcommand == "pull":
        if not args.model:
            print(f"{_red('❌')} Model name required.")
            return 1
        print(f"Pulling model '{args.model}'...")
        with Spinner(f"Pulling {args.model}..."):
            ok = pull_ollama_model(args.model, timeout=args.timeout)
        if ok:
            print(f"{_green('✅')} Model '{args.model}' pulled successfully.")
        else:
            print(f"{_red('❌')} Failed to pull model '{args.model}'.")
            return 1
        return 0

    if args.subcommand == "rm":
        if not args.model:
            print(f"{_red('❌')} Model name required.")
            return 1
        if _ask_confirm(f"Remove model '{args.model}'?", default=False):
            ok = remove_ollama_model(args.model)
            if ok:
                print(f"{_green('✅')} Model '{args.model}' removed.")
            else:
                print(f"{_red('❌')} Failed to remove model '{args.model}'.")
                return 1
        return 0

    if args.subcommand == "info":
        if not args.model:
            print(f"{_red('❌')} Model name required.")
            return 1
        with Spinner(f"Fetching info for {args.model}..."):
            info = get_ollama_model_info(args.model)
        if info:
            print(f"\n{_bold('📋 Model Info')}: {args.model}\n")
            for key, value in info.items():
                if key not in ("model", "modelfile"):
                    print(f"  {key}: {value}")
            print()
        else:
            print(f"{_red('❌')} Failed to get info for '{args.model}'.")
            return 1
        return 0

    print(f"{_red('❌')} Unknown subcommand: {args.subcommand}")
    return 1


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oc",
        description=f"{BANNER}\nLaunch, manage, and wrangle OpenCode instances from the comfort of your terminal.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  oc launch                                    # Interactive wizard\n"
            "  oc launch --config myproject.json            # From config file\n"
            "  oc launch -m qwen2.5-coder:32b -d ~/src -a coding  # Direct\n"
            "  oc launch -m gpt-4o --model-type cloud -d .  # Cloud model\n"
            "  oc status                                    # Check instances\n"
            "  oc resume                                    # Resume session\n"
            "  oc resume --new_location ~/other_project     # Resume elsewhere\n"
            "  oc kill-all                                  # Nuke everything\n"
            "  oc init                                      # Generate config\n"
            "  oc restart                                   # Restart stopped instance\n"
            "  oc logs                                      # View instance logs\n"
            "  oc config-save myproject                     # Save config preset\n"
            "  oc config-load myproject                     # Load config preset\n"
            "  oc sessions                                  # Manage session history\n"
            "  oc ollama pull qwen2.5-coder:32b             # Pull Ollama model\n"
        ),
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("--version", action="version", version=f"oc {__version__}")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would happen without executing",
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # launch
    p_launch = sub.add_parser("launch", help="Launch new OpenCode instance(s)")
    p_launch.add_argument("-c", "--config", help="Path to JSON config file")
    p_launch.add_argument("-m", "--model", help="Model name")
    p_launch.add_argument(
        "--model-type",
        dest="model_type",
        choices=["local", "cloud"],
        help="Model type: local (Ollama) or cloud",
    )
    p_launch.add_argument("-d", "--dir", help="Working directory")
    p_launch.add_argument("-a", "--agent", help="Agent template slug")
    p_launch.add_argument("-t", "--terminal", help="Terminal emulator to use")
    p_launch.add_argument(
        "-n",
        "--count",
        type=int,
        default=1,
        help="Number of instances to launch (default: 1)",
    )

    # status
    sub.add_parser("status", help="Show all running instances")

    # stop
    p_stop = sub.add_parser("stop", help="Stop a specific instance")
    p_stop.add_argument(
        "instance_id", nargs="?", help="Instance ID (interactive if omitted)"
    )

    # kill-all
    sub.add_parser("kill-all", help="Stop ALL running instances")

    # resume
    p_resume = sub.add_parser("resume", help="Resume from session history")
    p_resume.add_argument(
        "--new_location", help="Apply session settings to this new directory"
    )

    # list-agents
    sub.add_parser("list-agents", help="Show available agent templates")

    # list-models
    sub.add_parser("list-models", help="Show available Ollama models")

    # init
    p_init = sub.add_parser("init", help="Generate default config interactively")
    p_init.add_argument(
        "-o",
        "--output",
        help="Path to write config (default: ~/.config/opencode-launcher/config.json)",
    )

    # restart
    p_restart = sub.add_parser("restart", help="Restart a stopped instance")
    p_restart.add_argument(
        "instance_id", nargs="?", help="Instance ID to restart (interactive if omitted)"
    )

    # logs
    p_logs = sub.add_parser("logs", help="View instance logs")
    p_logs.add_argument(
        "instance_id", nargs="?", help="Instance ID (interactive if omitted)"
    )
    p_logs.add_argument(
        "-n", "--lines", type=int, default=50, help="Number of lines to show"
    )
    p_logs.add_argument(
        "-f",
        "--follow",
        action="store_true",
        help="Follow output (not yet implemented)",
    )

    # config-save
    p_csave = sub.add_parser("config-save", help="Save config preset")
    p_csave.add_argument("name", nargs="?", help="Preset name")
    p_csave.add_argument("-m", "--model", help="Model name")
    p_csave.add_argument("--model-type", dest="model_type", choices=["local", "cloud"])
    p_csave.add_argument("-d", "--dir", help="Working directory")
    p_csave.add_argument("-a", "--agent", help="Agent slug")
    p_csave.add_argument("-t", "--terminal", help="Terminal")
    p_csave.add_argument("--list", action="store_true", help="List all presets")
    p_csave.add_argument(
        "--export", action="store_true", help="Export all presets as base64"
    )

    # config-load
    p_cload = sub.add_parser("config-load", help="Load config preset")
    p_cload.add_argument("name", nargs="?", help="Preset name")
    p_cload.add_argument("--list", action="store_true", help="List all presets")
    p_cload.add_argument("--delete", action="store_true", help="Delete the preset")
    p_cload.add_argument(
        "--import", dest="import_data", help="Import from base64 string"
    )
    p_cload.add_argument("--override", nargs="*", help="Override settings (key=value)")

    # sessions
    p_sess = sub.add_parser("sessions", help="Manage session history")
    p_sess.add_argument("--clear", action="store_true", help="Clear all history")
    p_sess.add_argument("--export", help="Export to JSON file")
    p_sess.add_argument("--import", dest="import_file", help="Import from JSON file")

    # ollama
    p_ollama = sub.add_parser("ollama", help="Manage Ollama models")
    p_ollama.add_argument(
        "subcommand", nargs="?", choices=["list", "pull", "rm", "info"]
    )
    p_ollama.add_argument("model", nargs="?", help="Model name (for pull/rm/info)")
    p_ollama.add_argument(
        "--timeout", type=int, default=300, help="Timeout for pull (seconds)"
    )

    return parser


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

COMMANDS = {
    "launch": cmd_launch,
    "status": cmd_status,
    "stop": cmd_stop,
    "kill-all": cmd_kill_all,
    "resume": cmd_resume,
    "list-agents": cmd_list_agents,
    "list-models": cmd_list_models,
    "init": cmd_init,
    "restart": cmd_restart,
    "logs": cmd_logs,
    "config-save": cmd_config_save,
    "config-load": cmd_config_load,
    "sessions": cmd_sessions,
    "ollama": cmd_ollama,
}


def main():
    parser = build_parser()
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)-8s %(message)s" if args.verbose else "%(message)s",
    )

    # Ensure LOGS_DIR exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Propagate --dry-run to subcommands that support it
    if hasattr(args, "dry_run") and args.dry_run:
        pass  # Already handled in cmd_launch

    if not args.command:
        print(BANNER)
        parser.print_help()
        return 0

    handler = COMMANDS.get(args.command)
    if handler:
        return handler(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main() or 0)

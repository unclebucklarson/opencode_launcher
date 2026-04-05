#!/usr/bin/env python3
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
import logging
import sys
from pathlib import Path

from . import __version__
from .constants import BANNER
from .config import load_config, validate_config, ensure_dirs
from .models import is_ollama_running, get_ollama_models, validate_local_model_constraint
from .terminals import detect_terminals, get_preferred_terminal, launch_in_terminal
from .sessions import add_session, get_sessions, format_session
from .instances import (
    add_instance, get_instances, stop_instance, kill_all,
    format_instance, get_running_local_models,
)
from .agents import list_agents, get_agent_slugs, get_agent_path, format_agent

log = logging.getLogger("oc")

# ---------------------------------------------------------------------------
# TUI helpers (questionary) - graceful fallback to input() if not installed
# ---------------------------------------------------------------------------

_HAS_QUESTIONARY = False
try:
    import questionary
    from questionary import Style

    _Q_STYLE = Style([
        ("qmark", "fg:cyan bold"),
        ("question", "bold"),
        ("answer", "fg:green bold"),
        ("pointer", "fg:cyan bold"),
        ("highlighted", "fg:cyan bold"),
        ("selected", "fg:green"),
    ])
    _HAS_QUESTIONARY = True
except ImportError:
    pass


def _ask_select(message: str, choices: list[str], default: str | None = None) -> str:
    """Prompt user to select from a list."""
    if _HAS_QUESTIONARY:
        return questionary.select(message, choices=choices, default=default, style=_Q_STYLE).ask()
    print(f"\n{message}")
    for i, c in enumerate(choices):
        print(f"  [{i}] {c}")
    while True:
        try:
            idx = int(input("Enter number: ").strip())
            if 0 <= idx < len(choices):
                return choices[idx]
        except (ValueError, EOFError):
            pass
        print("Invalid selection, try again.")


def _ask_text(message: str, default: str = "") -> str:
    """Prompt user for text input."""
    if _HAS_QUESTIONARY:
        return questionary.text(message, default=default, style=_Q_STYLE).ask()
    result = input(f"{message} [{default}]: ").strip()
    return result if result else default


def _ask_confirm(message: str, default: bool = True) -> bool:
    """Prompt user for yes/no."""
    if _HAS_QUESTIONARY:
        return questionary.confirm(message, default=default, style=_Q_STYLE).ask()
    yn = input(f"{message} [{'Y/n' if default else 'y/N'}]: ").strip().lower()
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
        if not config_data:
            print(f"❌ Could not load config: {args.config}")
            return 1
        errors = validate_config(config_data)
        if errors:
            for e in errors:
                print(f"  ⚠️  {e}")

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
                print("❌ Ollama is not running! Start it with: ollama serve")
                return 1
            models = get_ollama_models()
            if not models:
                print("❌ No models found in Ollama. Pull one with: ollama pull <model>")
                return 1
            model = _ask_select("Select Ollama model:", choices=models)
        else:
            model = _ask_text("Enter cloud model name (e.g., anthropic/claude-3.5-sonnet):")
            if not model:
                print("❌ Model name is required.")
                return 1

    # --- Enforce local model constraint ---
    if model_type == "local":
        running_models = get_running_local_models()
        constraint_err = validate_local_model_constraint(model, running_models)
        if constraint_err:
            print(f"❌ {constraint_err}")
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
            print("❌ Aborted.")
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
            print("ℹ️  No agent templates found. Launching without agent.")

    # --- Terminal ---
    terminal = args.terminal or config_data.get("terminal")
    if not terminal:
        available = detect_terminals()
        if not available:
            print("❌ No supported terminal emulators found!")
            print("   Install one of: terminator, gnome-terminal, konsole, xterm")
            return 1
        if len(available) == 1:
            terminal = available[0]
            print(f"ℹ️  Using terminal: {terminal}")
        else:
            preferred = get_preferred_terminal(available)
            terminal = _ask_select(
                "Select terminal emulator:",
                choices=available,
                default=preferred,
            )

    # --- Number of instances ---
    count = args.count or 1

    # --- Build OpenCode command ---
    oc_cmd_parts = ["opencode"]
    if agent_slug:
        agent_path = get_agent_path(agent_slug)
        if agent_path:
            oc_cmd_parts.extend(["--agent", str(agent_path)])
    # Note: OpenCode model config is handled via its own config, not CLI flags typically.
    # We set it via environment or config file. For now, include as info.
    oc_cmd = " ".join(oc_cmd_parts)

    print(f"\n🚀 Launching {count} instance(s)...")
    print(f"   Model:     {model_type}:{model}")
    print(f"   Directory: {directory}")
    print(f"   Agent:     {agent_slug or '(none)'}")
    print(f"   Terminal:  {terminal}")
    print()

    for i in range(count):
        title = f"OpenCode [{i+1}/{count}] - {agent_slug or 'default'} @ {Path(directory).name}"
        pid = launch_in_terminal(terminal, title, directory, oc_cmd)
        if pid:
            iid = add_instance(pid, model, directory, agent_slug or "", terminal, model_type)
            print(f"  ✅ Instance {iid} started (PID {pid})")
        else:
            print(f"  ❌ Failed to launch instance {i+1}")

    # Record session
    add_session(model, directory, agent_slug or "", terminal, model_type)
    print("\n✨ Done! Use 'oc status' to check running instances.")
    return 0


def cmd_status(args):
    """Show all running instances."""
    instances = get_instances()
    if not instances:
        print("No running instances. 🍃")
        return 0
    print(f"\n📊 Running Instances ({len(instances)}):\n")
    for iid, info in instances.items():
        print(format_instance(iid, info))
        print()
    return 0


def cmd_stop(args):
    """Stop a specific instance."""
    if not args.instance_id:
        # Show instances and let user pick
        instances = get_instances()
        if not instances:
            print("No running instances.")
            return 0
        choices = [f"{iid} - {info.get('model', '?')} @ {info.get('directory', '?')}"
                   for iid, info in instances.items()]
        selected = _ask_select("Select instance to stop:", choices=choices)
        instance_id = selected.split(" - ")[0].strip()
    else:
        instance_id = args.instance_id

    ok, msg = stop_instance(instance_id)
    print(f"{'✅' if ok else '❌'} {msg}")
    return 0 if ok else 1


def cmd_kill_all(args):
    """Kill all running instances."""
    if not _ask_confirm("Kill ALL running instances?", default=False):
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
    idx = int(selected.split("]")[0].replace("[", "").strip())
    session = sessions[idx]

    # Apply new location if requested
    directory = session["directory"]
    if args.new_location:
        directory = str(Path(args.new_location).expanduser().resolve())
        if not Path(directory).exists():
            if _ask_confirm(f"Directory '{directory}' doesn't exist. Create it?"):
                Path(directory).mkdir(parents=True, exist_ok=True)
            else:
                print("❌ Aborted.")
                return 1
        print(f"ℹ️  Using new location: {directory}")

    # Create a fake args namespace and delegate to launch
    launch_args = argparse.Namespace(
        config=None,
        model_type=session.get("model_type", "local"),
        model=session["model"],
        dir=directory,
        agent=session.get("agent") or None,
        terminal=session.get("terminal") or None,
        count=1,
    )
    return cmd_launch(launch_args)


def cmd_list_agents(args):
    """List available agent templates."""
    agents = list_agents()
    if not agents:
        print("No agent templates found.")
        print(f"Add .md files to: ~/.config/opencode-launcher/agents/")
        return 0
    print("\n📋 Available Agents:\n")
    print(f"  {'SLUG':20s} {'NAME':25s} DESCRIPTION")
    print(f"  {'─'*20} {'─'*25} {'─'*40}")
    for a in agents:
        print(format_agent(a))
    print()
    return 0


def cmd_list_models(args):
    """List available Ollama models."""
    if not is_ollama_running():
        print("❌ Ollama is not running! Start it with: ollama serve")
        return 1
    models = get_ollama_models()
    if not models:
        print("No models found. Pull one with: ollama pull <model>")
        return 0
    print(f"\n🤖 Available Ollama Models ({len(models)}):\n")
    for m in models:
        print(f"  • {m}")
    print()
    return 0


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
        ),
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("--version", action="version", version=f"oc {__version__}")

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # launch
    p_launch = sub.add_parser("launch", help="Launch new OpenCode instance(s)")
    p_launch.add_argument("-c", "--config", help="Path to JSON config file")
    p_launch.add_argument("-m", "--model", help="Model name")
    p_launch.add_argument("--model-type", dest="model_type", choices=["local", "cloud"],
                          help="Model type: local (Ollama) or cloud")
    p_launch.add_argument("-d", "--dir", help="Working directory")
    p_launch.add_argument("-a", "--agent", help="Agent template slug")
    p_launch.add_argument("-t", "--terminal", help="Terminal emulator to use")
    p_launch.add_argument("-n", "--count", type=int, default=1,
                          help="Number of instances to launch (default: 1)")

    # status
    sub.add_parser("status", help="Show all running instances")

    # stop
    p_stop = sub.add_parser("stop", help="Stop a specific instance")
    p_stop.add_argument("instance_id", nargs="?", help="Instance ID (interactive if omitted)")

    # kill-all
    sub.add_parser("kill-all", help="Stop ALL running instances")

    # resume
    p_resume = sub.add_parser("resume", help="Resume from session history")
    p_resume.add_argument("--new_location", help="Apply session settings to this new directory")

    # list-agents
    sub.add_parser("list-agents", help="Show available agent templates")

    # list-models
    sub.add_parser("list-models", help="Show available Ollama models")

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
}


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)-8s %(message)s" if args.verbose else "%(message)s",
    )

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

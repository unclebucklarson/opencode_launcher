# AGENTS.md — OpenCode Launcher

## Project

Python 3.10+ CLI (`oc`) that launches and orchestrates multiple [OpenCode](https://opencode.ai) instances in separate terminal windows.

## Commands

```bash
bash install.sh          # recommended: installs deps, editable package, and ~/.local/bin/oc wrapper
pip install -e .         # alternative install
python -m opencode_launcher launch   # run without installing
```

14 subcommands: `launch`, `status`, `stop`, `kill-all`, `resume`, `list-agents`, `list-models`, `init`, `restart`, `logs`, `config-save`, `config-load`, `sessions`, `ollama`.

## Architecture

Single flat package — `opencode_launcher/` with 8 modules:

| Module | Responsibility |
|--------|---------------|
| `cli.py` | argparse, TUI prompts (questionary with input() fallback), all command implementations |
| `config.py` | JSON config load/save/validate, .env support, config presets |
| `models.py` | Ollama API reachability check, model listing, local model constraint enforcement, retry logic |
| `terminals.py` | Detects available terminals, builds per-terminal launch commands |
| `instances.py` | PID-based instance tracking, stale cleanup, stop/kill/restart |
| `sessions.py` | Last-10 session history for resume |
| `agents.py` | Discovers `*.md` agent templates, parses YAML frontmatter, validation |
| `constants.py` | All paths, env vars, defaults |

## Config & State

All stored under `~/.config/opencode-launcher/` (override with `OC_CONFIG_DIR`):

```
~/.config/opencode-launcher/
├── agents/              # *.md agent templates (YAML frontmatter + markdown body)
├── sessions.json        # last 10 launch sessions
├── instances.json       # currently running instances (PID-tracked)
├── stopped_instances.json  # stopped instances available for restart
├── config.json          # optional default launch config
├── .env                 # optional environment overrides
├── presets/             # named config presets (*.json)
└── logs/                # instance output logs
```

Env vars: `OC_CONFIG_DIR`, `OLLAMA_API_URL` (default `http://localhost:11434`).

## Key Constraints

- **Single-model constraint (local only):** All running Ollama instances must use the same model. Launch is rejected if it would cause a model swap. Cloud models are exempt.
- **Cloud models require `--model-type cloud`:** Without this flag the launcher treats the model as local and tries to validate against Ollama.
- **Terminal detection order:** terminator > gnome-terminal > konsole > kitty > xterm. If only one is found, it's used automatically.
- **`oc` wrapper:** `install.sh` writes `~/.local/bin/oc` as `exec python3 -m opencode_launcher.cli "$@"` to avoid pyenv shim issues.
- **Terminator PID quirk:** Terminator forks and exits immediately, so the returned PID may not reflect the actual running session. Instance tracking handles stale PIDs gracefully via `is_pid_alive_and_same()` which checks process start time to detect PID reuse.
- **File locking:** All JSON file operations use `fcntl.flock()` to prevent race conditions.

## Agent Templates

- Slug = filename without `.md` extension (e.g., `coding.md` → slug `coding`)
- Frontmatter fields: `name`, `description`, `temperature` (default 0.5)
- Body after `---` is the system prompt passed to OpenCode via `--agent <path>`
- No restart needed when adding/editing — discovered on each launch
- Validated on load: missing required fields (`name`, `description`) produce warnings

## Dependencies

- `questionary>=2.0.0` — interactive TUI prompts
- `colorama>=0.4.6` — cross-platform colored output (optional, graceful fallback)

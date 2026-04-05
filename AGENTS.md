# AGENTS.md — OpenCode Launcher

## Project

Python 3.10+ CLI (`oc`) that launches and orchestrates multiple [OpenCode](https://opencode.ai) instances in separate terminal windows.

## Commands

```bash
bash install.sh          # recommended: installs deps, editable package, and ~ /.local/bin/oc wrapper
pip install -e .         # alternative install
python -m opencode_launcher launch   # run without installing
```

7 subcommands: `launch`, `status`, `stop`, `kill-all`, `resume`, `list-agents`, `list-models`.

## Architecture

Single flat package — `opencode_launcher/` with 7 modules:

| Module | Responsibility |
|--------|---------------|
| `cli.py` | argparse, TUI prompts (questionary with input() fallback), all command implementations |
| `config.py` | JSON config load/save/validate |
| `models.py` | Ollama API reachability check, model listing, local model constraint enforcement |
| `terminals.py` | Detects available terminals, builds per-terminal launch commands |
| `instances.py` | PID-based instance tracking, stale cleanup, stop/kill |
| `sessions.py` | Last-10 session history for resume |
| `agents.py` | Discovers `*.md` agent templates, parses YAML frontmatter |
| `constants.py` | All paths, env vars, defaults |

## Config & State

All stored under `~/.config/opencode-launcher/` (override with `OC_CONFIG_DIR`):

```
~/.config/opencode-launcher/
├── agents/          # *.md agent templates (YAML frontmatter + markdown body)
├── sessions.json    # last 10 launch sessions
├── instances.json   # currently running instances (PID-tracked)
└── config.json      # optional default launch config
```

Env vars: `OC_CONFIG_DIR`, `OLLAMA_API_URL` (default `http://localhost:11434`).

## Key Constraints

- **Single-model constraint (local only):** All running Ollama instances must use the same model. Launch is rejected if it would cause a model swap. Cloud models are exempt.
- **Cloud models require `--model-type cloud`:** Without this flag the launcher treats the model as local and tries to validate against Ollama.
- **Terminal detection order:** terminator > gnome-terminal > konsole > xterm. If only one is found, it's used automatically.
- **`oc` wrapper:** `install.sh` writes `~/.local/bin/oc` as `exec python3 -m opencode_launcher.cli "$@"` to avoid pyenv shim issues.

## Agent Templates

- Slug = filename without `.md` extension (e.g., `coding.md` → slug `coding`)
- Frontmatter fields: `name`, `description`, `temperature` (default 0.5)
- Body after `---` is the system prompt passed to OpenCode via `--agent <path>`
- No restart needed when adding/editing — discovered on each launch

## Testing

No test suite exists. Verify manually:

```bash
oc --version          # sanity check
oc list-agents        # verify agent discovery
oc list-models        # verify Ollama connectivity (requires ollama serve)
oc launch --help      # verify argparse wiring
```

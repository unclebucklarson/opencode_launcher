# AGENTS.md — OpenCode Launcher

## Project

Python 3.10+ CLI (`oc`) that launches and orchestrates multiple [OpenCode](https://opencode.ai) instances in separate terminal windows.

## Commands

```bash
bash install.sh          # recommended: installs deps, editable package, and ~/.local/bin/oc wrapper
pip install -e .         # alternative install
python -m opencode_launcher launch   # run without installing
```

13 subcommands: `launch`, `status`, `stop`, `kill-all`, `resume`, `list-agents`, `list-models`, `init`, `restart`, `logs`, `config-save`, `config-load`, `sessions`.

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
├── agents/          # *.md agent templates (YAML frontmatter + markdown body)
├── sessions.json    # last 10 launch sessions
├── instances.json   # currently running instances (PID-tracked)
├── config.json      # optional default launch config
├── .env             # optional environment overrides
└── presets/         # named config presets (*.json)
```

Env vars: `OC_CONFIG_DIR`, `OLLAMA_API_URL` (default `http://localhost:11434`).

## Key Constraints

- **Single-model constraint (local only):** All running Ollama instances must use the same model. Launch is rejected if it would cause a model swap. Cloud models are exempt.
- **Cloud models require `--model-type cloud`:** Without this flag the launcher treats the model as local and tries to validate against Ollama.
- **Terminal detection order:** terminator > gnome-terminal > konsole > kitty > xterm. If only one is found, it's used automatically.
- **`oc` wrapper:** `install.sh` writes `~/.local/bin/oc` as `exec python3 -m opencode_launcher.cli "$@"` to avoid pyenv shim issues.

## Agent Templates

- Slug = filename without `.md` extension (e.g., `coding.md` → slug `coding`)
- Frontmatter fields: `name`, `description`, `temperature` (default 0.5)
- Body after `---` is the system prompt passed to OpenCode via `--agent <path>`
- No restart needed when adding/editing — discovered on each launch
- Validated on load: missing required fields produce warnings

## Bug Fixes (Completed)

All 17 identified issues have been resolved:

| # | Issue | Fix |
|---|-------|-----|
| 1 | Model not passed to OpenCode | Added `--model` flag to OpenCode command |
| 2 | Unquoted paths in terminals | Paths now properly quoted for spaces |
| 3 | `_ask_select` default=None crash | Default handled when not in choices |
| 4 | Questionary None on cancel | Added `sys.exit(0)` on cancel |
| 5 | Session resume bounds check | Added bounds validation |
| 6 | Config validation non-fatal | Validation errors now abort launch |
| 7 | Race condition on JSON files | Added `fcntl` file locking |
| 8 | load_config crash on missing | Returns None for missing files |
| 9 | PID reuse vulnerability | Added `is_pid_alive_and_same()` check |
| 10 | install.sh bare pip | Changed to `python3 -m pip` |
| 11 | Hardcoded version in banner | Removed version from ASCII art |
| 12 | Agent frontmatter parser | Added quote stripping for values |
| 13 | count >= 1 validation | Rejects zero/negative counts |
| 14 | kill-all confirmation fix | Fixed confirmation handling |
| 15-17 | Unused imports | Cleaned up |

**Bonus:** Fixed broken package structure — modules moved from root into `opencode_launcher/` subdirectory.

## Planned Improvements

### Phase 1: Foundation
| Item | Status | Description |
|------|--------|-------------|
| Kitty terminal support | ✅ | Added `kitty` to terminal preferences |
| Ollama retry logic | ✅ | Exponential backoff for API calls |
| `oc init` command | ✅ | Generate default config interactively |

### Phase 2: Usability
| Item | Status | Description |
|------|--------|-------------|
| Model filtering in TUI | ✅ | Typeahead search for model selection |
| `.env` file support | ✅ | Load env vars from `.env` in config dir |
| `oc restart` command | ✅ | Restart a stopped instance |
| Agent validation | ✅ | Validate frontmatter on load |

### Phase 3: Polish
| Item | Status | Description |
|------|--------|-------------|
| Colored output | ✅ | Cross-platform colors via `colorama` |
| Progress indicators | ✅ | Spinner during Ollama queries |
| `oc logs` command | ✅ | View recent instance output |
| `--dry-run` mode | ✅ | Preview what `launch` would do |

### Phase 4: Advanced
| Item | Status | Description |
|------|--------|-------------|
| Config presets | ✅ | `oc config-save/load` for named configs |
| Team export/import | ✅ | Share configs via base64 encode |
| Hooks support | ✅ | Pre/post launch hooks |
| Ollama management | ✅ | `oc ollama pull/list/rm` commands |

## Testing

No test suite exists. Verify manually:

```bash
oc --version          # sanity check
oc list-agents        # verify agent discovery
oc list-models        # verify Ollama connectivity (requires ollama serve)
oc launch --help      # verify argparse wiring
```

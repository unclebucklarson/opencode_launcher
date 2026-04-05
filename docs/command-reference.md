# Command Reference

The complete guide to every `oc` command, flag, and option.

---

### Table of Contents

- [Global Options](#global-options)
- [oc launch](#oc-launch)
- [oc status](#oc-status)
- [oc stop](#oc-stop)
- [oc kill-all](#oc-kill-all)
- [oc resume](#oc-resume)
- [oc list-agents](#oc-list-agents)
- [oc list-models](#oc-list-models)
- [oc init](#oc-init)
- [oc restart](#oc-restart)
- [oc logs](#oc-logs)
- [oc config-save](#oc-config-save)
- [oc config-load](#oc-config-load)
- [oc sessions](#oc-sessions)
- [oc ollama](#oc-ollama)

---

### Global Options

These flags work with any command:

| Flag | Description |
|------|-------------|
| `-v`, `--verbose` | Enable debug logging |
| `--version` | Show version number and exit |
| `--dry-run` | Preview what would happen without executing |
| `-h`, `--help` | Show help message and exit |

```bash
oc --version      # Print version
oc -v launch      # Launch with debug output
oc --help         # Show global help
oc launch --help  # Show help for 'launch' command
oc --dry-run launch -m qwen2.5-coder:32b -d ~/project  # Preview launch
```

---

### `oc launch`

Launch one or more new OpenCode instances.

#### Synopsis

```bash
oc launch [OPTIONS]
```

#### Options

| Flag | Long Form | Description |
|------|-----------|-------------|
| `-c` | `--config FILE` | Path to a JSON config file |
| `-m` | `--model NAME` | Model name (e.g., `qwen2.5-coder:32b`) |
| | `--model-type TYPE` | `local` (Ollama) or `cloud` |
| `-d` | `--dir PATH` | Working directory for the instance |
| `-a` | `--agent SLUG` | Agent template slug (e.g., `coding`) |
| `-t` | `--terminal NAME` | Terminal emulator to use |
| `-n` | `--count N` | Number of instances to launch (default: 1) |
| | `--dry-run` | Preview what would be launched |
| | `--no-hooks` | Skip pre/post launch hooks |

#### Modes of Operation

##### Interactive Mode (no flags)
```bash
oc launch
```
Launches the TUI wizard that walks you through model source, model, directory, agent, and terminal selection. Model selection now includes typeahead filtering for quick searching.

##### Config File Mode
```bash
oc launch --config myproject.json
```
Loads all settings from a JSON file. Missing fields trigger interactive prompts. See [Configuration](configuration.md) for the config file format.

##### CLI Flags Mode
```bash
oc launch -m qwen2.5-coder:32b -d ~/src/project -a coding
```
Pass settings directly. Missing required fields trigger interactive prompts for just those fields.

##### Combined Mode
```bash
oc launch --config base.json -d ~/src/override_dir
```
CLI flags override config file values.

##### Dry Run Mode
```bash
oc launch --dry-run -m qwen2.5-coder:32b -d ~/src/project -a coding -n 3
```
Shows exactly what would be launched without actually opening any terminals.

#### Examples

```bash
# Interactive wizard
oc launch

# Local model, specific project, coding agent
oc launch -m qwen2.5-coder:32b -d ~/src/myapp -a coding

# Cloud model
oc launch -m anthropic/claude-3.5-sonnet --model-type cloud -d ~/src/myapp

# Launch 3 instances (same model, same dir)
oc launch -m qwen2.5-coder:32b -d ~/src/myapp -n 3

# From config file
oc launch --config ~/configs/data-analysis.json

# Config + override the directory
oc launch --config ~/configs/base.json -d ~/src/different_project

# Specific terminal
oc launch -m qwen2.5-coder:32b -d . -t gnome-terminal

# Dry run — preview without launching
oc launch --dry-run -m qwen2.5-coder:32b -d ~/src/myapp -a coding
```

---

### `oc status`

Show all currently running OpenCode instances.

#### Synopsis

```bash
oc status
```

#### Details

- Automatically cleans up stale instances (PIDs that are no longer running)
- Shows instance ID, PID, model, agent, directory, terminal, and start time
- Displays 🟢 for running and 🔴 for stopped instances

#### Output Example

```
📊 Running Instances (2):

  a3f7b2c1 | 🟢 running | PID 12345
    Model: local:qwen2.5-coder:32b | Agent: coding
    Dir:   /home/you/src/project
    Term:  terminator | Started: 2026-04-05 14:30

  b8e2d4f6 | 🟢 running | PID 12346
    Model: local:qwen2.5-coder:32b | Agent: analyst
    Dir:   /home/you/src/data
    Term:  terminator | Started: 2026-04-05 14:32
```

---

### `oc stop`

Stop a specific running instance.

#### Synopsis

```bash
oc stop [INSTANCE_ID]
```

#### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `INSTANCE_ID` | No | The 8-character instance ID. If omitted, shows an interactive picker. |

#### Examples

```bash
# Interactive — pick from a list
oc stop

# Direct — stop by ID
oc stop a3f7b2c1
```

#### Behavior

- Sends `SIGTERM` to the terminal process
- Removes the instance from tracking
- If the PID is already dead, cleans up the stale entry

---

### `oc kill-all`

Terminate **all** running instances. The nuclear option.

#### Synopsis

```bash
oc kill-all
```

#### Behavior

- Prompts for confirmation before proceeding (default: No)
- Sends `SIGTERM` to every tracked instance
- Cleans up the instance registry
- Reports status for each instance

#### Example

```bash
$ oc kill-all
? Kill ALL running instances? (y/N) y
  🔪 Killed 'a3f7b2c1' (PID 12345)
  🔪 Killed 'b8e2d4f6' (PID 12346)
All clear! 🧹
```

---

### `oc resume`

Resume a previous session from history.

#### Synopsis

```bash
oc resume [OPTIONS]
```

#### Options

| Flag | Description |
|------|-------------|
| `--new_location PATH` | Apply the session's settings to a different directory |

#### Details

- Shows your last 10 sessions, newest first
- Each entry shows: timestamp, model type, model name, agent, and directory
- Selecting a session re-launches with the same settings
- Use `--new_location` to keep the model/agent but change the directory

#### Examples

```bash
# Pick from session history
oc resume

# Resume session but in a different directory
oc resume --new_location ~/src/new_project
```

#### Session Display Format

```
? Select session to resume:
❯ [0] 2026-04-05 14:30 | local:qwen2.5-coder:32b | coding | /home/you/src/project
  [1] 2026-04-04 10:15 | cloud:anthropic/claude-3.5-sonnet | analyst | /home/you/data
  [2] 2026-04-03 09:00 | local:qwen2.5-coder:32b | general | /home/you/scratch
```

---

### `oc list-agents`

Display all available agent templates.

#### Synopsis

```bash
oc list-agents
```

#### Output Example

```
📋 Available Agents:

  SLUG                 NAME                      DESCRIPTION
  ──────────────────── ───────────────────────── ────────────────────────────────────────
  analyst              Data Analyst               Data analysis and insights extraction
  coding               Software Developer         Software development, architecture, and implementation agent
  general              General Assistant           General purpose assistant
  qa                   QA Engineer                Quality assurance and testing
  technical-writer     Technical Writer            Documentation and technical writing
```

---

### `oc list-models`

List all models available in your local Ollama instance.

#### Synopsis

```bash
oc list-models
```

#### Requirements

- Ollama must be running (`ollama serve`)

#### Output Example

```
🤖 Available Ollama Models (3):

  • deepseek-coder:33b
  • llama3:8b
  • qwen2.5-coder:32b
```

---

### `oc init`

Generate a default configuration file interactively.

#### Synopsis

```bash
oc init [OPTIONS]
```

#### Options

| Flag | Description |
|------|-------------|
| `-o`, `--output FILE` | Path to write the config (default: `~/.config/opencode-launcher/config.json`) |
| `--preset NAME` | Start from a named preset instead of blank |

#### Details

- Walks through all config fields with sensible defaults
- Validates inputs as you go
- Can be used to create project-specific configs

#### Examples

```bash
# Interactive wizard for default config
oc init

# Save to a specific location
oc init -o ~/configs/myproject.json

# Start from a preset and customize
oc init --preset data-science
```

---

### `oc restart`

Restart a stopped instance with the same settings.

#### Synopsis

```bash
oc restart [INSTANCE_ID]
```

#### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `INSTANCE_ID` | No | The instance ID to restart. If omitted, shows an interactive picker of stopped instances. |

#### Details

- Only works for instances that have been stopped (not killed)
- Reuses the same model, directory, agent, and terminal settings
- Creates a new instance ID and PID

#### Examples

```bash
# Interactive — pick from stopped instances
oc restart

# Direct — restart by ID
oc restart a3f7b2c1
```

---

### `oc logs`

View recent output from a running or recently stopped instance.

#### Synopsis

```bash
oc logs [INSTANCE_ID] [OPTIONS]
```

#### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `INSTANCE_ID` | No | The instance ID. If omitted, shows an interactive picker. |

#### Options

| Flag | Description |
|------|-------------|
| `-n`, `--lines N` | Number of lines to show (default: 50) |
| `-f`, `--follow` | Follow output in real-time (like `tail -f`) |

#### Details

- Shows the most recent output from the instance's terminal log
- Only available for instances that were launched with logging enabled
- Logs are stored in `~/.config/opencode-launcher/logs/`

#### Examples

```bash
# Interactive — pick an instance
oc logs

# Direct — view logs by ID
oc logs a3f7b2c1

# Show last 100 lines
oc logs a3f7b2c1 -n 100

# Follow output in real-time
oc logs a3f7b2c1 -f
```

---

### `oc config-save`

Save the current launch settings as a named config preset.

#### Synopsis

```bash
oc config-save NAME [OPTIONS]
```

#### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `NAME` | Yes | Name for the preset (alphanumeric + hyphens) |

#### Options

| Flag | Description |
|------|-------------|
| `-m`, `--model NAME` | Model name |
| `--model-type TYPE` | `local` or `cloud` |
| `-d`, `--dir PATH` | Working directory |
| `-a`, `--agent SLUG` | Agent template slug |
| `-t`, `--terminal NAME` | Terminal emulator |

#### Examples

```bash
# Save current interactive settings
oc config-save my-project

# Save with explicit settings
oc config-save backend -m qwen2.5-coder:32b -d ~/src/backend -a coding

# List all saved presets
oc config-save --list
```

---

### `oc config-load`

Load a saved config preset and launch with it.

#### Synopsis

```bash
oc config-load NAME [OPTIONS]
```

#### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `NAME` | Yes | Name of the preset to load |

#### Options

| Flag | Description |
|------|-------------|
| `--override KEY=VALUE` | Override a specific setting |
| `--delete` | Delete the preset instead of loading it |

#### Examples

```bash
# Load and launch with a preset
oc config-load my-project

# Load preset but override the directory
oc config-load backend -d ~/src/backend-v2

# Delete a preset
oc config-load old-project --delete

# List all presets
oc config-load --list
```

---

### `oc sessions`

Manage session history.

#### Synopsis

```bash
oc sessions [OPTIONS]
```

#### Options

| Flag | Description |
|------|-------------|
| `--clear` | Clear all session history |
| `--export FILE` | Export sessions to a JSON file |
| `--import FILE` | Import sessions from a JSON file |

#### Details

- Shows all saved sessions (beyond the last 10 used by `oc resume`)
- Sessions are kept in `~/.config/opencode-launcher/sessions.json`
- Max 10 sessions stored (oldest are automatically pruned)

#### Examples

```bash
# View session history
oc sessions

# Clear all history
oc sessions --clear

# Export for backup
oc sessions --export ~/backup/sessions.json

# Import from backup
oc sessions --import ~/backup/sessions.json
```

---

### `oc ollama`

Manage Ollama models directly from the launcher.

#### Synopsis

```bash
oc ollama SUBCOMMAND [OPTIONS]
```

#### Subcommands

| Subcommand | Description |
|------------|-------------|
| `list` | List available local models (alias for `oc list-models`) |
| `pull MODEL` | Pull a model from Ollama |
| `rm MODEL` | Remove a local model |
| `info MODEL` | Show details about a model |

#### Options

| Flag | Description |
|------|-------------|
| `--timeout SECONDS` | Timeout for API requests (default: 30) |

#### Examples

```bash
# List models
oc ollama list

# Pull a new model
oc ollama pull qwen2.5-coder:32b

# Remove a model
oc ollama rm deepseek-coder:33b

# Show model info
oc ollama info qwen2.5-coder:32b
```

---

### Command Quick Reference

```
oc launch                                     # Interactive wizard
oc launch -c config.json                      # From config
oc launch -m MODEL -d DIR -a AGENT            # Direct flags
oc launch -m MODEL -d DIR -n 3                # Multiple instances
oc launch -m MODEL --model-type cloud -d DIR  # Cloud model
oc launch --dry-run -m MODEL -d DIR           # Preview without launching
oc status                                     # Show running instances
oc stop                                       # Interactive stop
oc stop INSTANCE_ID                           # Stop by ID
oc kill-all                                   # Stop everything
oc restart                                    # Restart a stopped instance
oc resume                                     # Resume from history
oc resume --new_location DIR                  # Resume elsewhere
oc list-agents                                # Show agents
oc list-models                                # Show Ollama models
oc init                                       # Generate config interactively
oc logs [ID]                                  # View instance logs
oc config-save NAME                           # Save config preset
oc config-load NAME                           # Load config preset
oc sessions                                   # Manage session history
oc ollama pull MODEL                          # Pull Ollama model
oc ollama rm MODEL                            # Remove Ollama model
oc --version                                  # Version info
oc -v COMMAND                                 # Verbose mode
oc --dry-run COMMAND                          # Dry run mode
```

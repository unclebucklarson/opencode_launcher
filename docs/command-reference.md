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

---

### Global Options

These flags work with any command:

| Flag | Description |
|------|-------------|
| `-v`, `--verbose` | Enable debug logging |
| `--version` | Show version number and exit |
| `-h`, `--help` | Show help message and exit |

```bash
oc --version      # Print version
oc -v launch      # Launch with debug output
oc --help         # Show global help
oc launch --help  # Show help for 'launch' command
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

#### Modes of Operation

##### Interactive Mode (no flags)
```bash
oc launch
```
Launches the TUI wizard that walks you through model source, model, directory, agent, and terminal selection.

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

### Command Quick Reference

```
oc launch                                     # Interactive wizard
oc launch -c config.json                      # From config
oc launch -m MODEL -d DIR -a AGENT            # Direct flags
oc launch -m MODEL -d DIR -n 3                # Multiple instances
oc launch -m MODEL --model-type cloud -d DIR  # Cloud model
oc status                                     # Show running instances
oc stop                                       # Interactive stop
oc stop INSTANCE_ID                           # Stop by ID
oc kill-all                                   # Stop everything
oc resume                                     # Resume from history
oc resume --new_location DIR                  # Resume elsewhere
oc list-agents                                # Show agents
oc list-models                                # Show Ollama models
oc --version                                  # Version info
oc -v COMMAND                                 # Verbose mode
```

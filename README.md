# OpenCode Launcher (`oc`)

A production-ready CLI tool for launching, managing, and orchestrating multiple [OpenCode](https://opencode.ai) instances from your terminal.

## Features

- **🚀 Launch Instances** — Spin up OpenCode in new terminal windows with one command
- **🤖 Model Selection** — Local Ollama dropdown or manual cloud model entry
- **🔒 Model Constraint** — Enforces single-model for all local Ollama instances (prevents model swapping)
- **📋 Agent Templates** — 5 curated agent templates (Analyst, QA, Coding, General, Technical Writer)
- **💾 Session History** — Remembers your last 10 sessions for quick resume
- **📊 Instance Tracking** — See what's running, stop individual instances, or nuke them all
- **🖥️ Terminal Detection** — Auto-detects terminator, gnome-terminal, konsole, xterm
- **🎨 Interactive TUI** — Pretty prompts via `questionary` with CLI fallback
- **📁 Config Files** — JSON configs for repeatable project setups

## Quick Start

```bash
# Install
cd opencode_launcher
bash install.sh

# Launch interactively
oc launch

# Launch with specific settings
oc launch -m qwen2.5-coder:32b -d ~/src/myproject -a coding

# Launch from config file
oc launch --config example_config.json

# Check running instances
oc status

# Resume a previous session
oc resume

# Resume in a different directory
oc resume --new_location ~/src/other_project
```

## Commands

| Command | Description |
|---------|-------------|
| `oc launch` | Launch new OpenCode instance(s) |
| `oc status` | Show all running instances |
| `oc stop [id]` | Stop a specific instance (interactive if no ID) |
| `oc kill-all` | Terminate all running instances |
| `oc resume` | Resume from session history |
| `oc list-agents` | List available agent templates |
| `oc list-models` | List available Ollama models |

## Launch Modes

### 1. Interactive (TUI)
```bash
oc launch
# Walks you through: model source → model → directory → agent → terminal
```

### 2. Config File
```bash
oc launch --config myproject.json
```

Config file format:
```json
{
  "model": "qwen2.5-coder:32b",
  "model_type": "local",
  "directory": "~/src/project1",
  "agent": "coding",
  "terminal": "terminator"
}
```

### 3. CLI Flags
```bash
# Local Ollama model
oc launch -m qwen2.5-coder:32b -d ~/src/project -a coding

# Cloud model
oc launch -m anthropic/claude-3.5-sonnet --model-type cloud -d ~/src/project

# Multiple instances
oc launch -m qwen2.5-coder:32b -d ~/src/project -n 3
```

### 4. Resume
```bash
# Pick from last 10 sessions
oc resume

# Apply previous settings to new directory
oc resume --new_location ~/src/new_project
```

## Agent Templates

Located in `~/.config/opencode-launcher/agents/`:

| Template | Description |
|----------|-------------|
| `analyst` | Data analysis and insights extraction |
| `qa` | Quality assurance and testing |
| `coding` | Software development |
| `general` | General purpose assistant |
| `technical-writer` | Documentation and technical writing |

Each agent is a Markdown file with YAML frontmatter:

```markdown
---
name: Software Developer
description: Software development, architecture, and implementation agent
temperature: 0.4
---

You are an experienced software developer...
```

### Adding Custom Agents

Drop a `.md` file into `~/.config/opencode-launcher/agents/` with the frontmatter format above. It'll show up automatically in `oc list-agents` and the launch wizard.

## Model Constraint

When using local Ollama models, **all running instances must use the same model**. This prevents Ollama from constantly swapping models in and out of VRAM.

```
❌ Instance 1: qwen2.5-coder:32b
   Instance 2: deepseek-coder:33b    ← REJECTED

✅ Instance 1: qwen2.5-coder:32b
   Instance 2: qwen2.5-coder:32b    ← OK
```

## File Layout

```
~/.config/opencode-launcher/
├── agents/
│   ├── analyst.md
│   ├── coding.md
│   ├── general.md
│   ├── qa.md
│   └── technical-writer.md
├── sessions.json       # Last 10 session history
├── instances.json      # Currently running instances
└── config.json         # Default config (optional)
```

## Requirements

- Python 3.10+
- `questionary` (installed automatically)
- A terminal emulator (terminator, gnome-terminal, konsole, or xterm)
- [OpenCode](https://opencode.ai) installed and in PATH
- [Ollama](https://ollama.ai) (for local models)

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OC_CONFIG_DIR` | `~/.config/opencode-launcher` | Config directory |
| `OLLAMA_API_URL` | `http://localhost:11434` | Ollama API base URL |

## Troubleshooting

**"Ollama is not running"** — Start Ollama: `ollama serve`

**"No supported terminal emulators found"** — Install one: `sudo apt install terminator`

**Instance shows as running but terminal is closed** — Run `oc status` (auto-cleans stale PIDs)

**`oc` command not found after install** — Add to PATH: `export PATH="${HOME}/.local/bin:${PATH}"`

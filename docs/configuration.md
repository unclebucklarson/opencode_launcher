# Configuration

All the knobs, switches, and dials for OpenCode Launcher.

---

### Table of Contents

- [Config File Format](#config-file-format)
- [Config File Location](#config-file-location)
- [Config Fields Reference](#config-fields-reference)
- [Environment Variables](#environment-variables)
- [Environment File (.env)](#environment-file-env)
- [Model Types](#model-types)
- [Model Constraint](#model-constraint)
- [Terminal Preferences](#terminal-preferences)
- [Config Precedence](#config-precedence)
- [Config Presets](#config-presets)
- [JSON Schema](#json-schema)

---

### Config File Format

Config files are plain JSON. Here's a full example:

```json
{
  "model": "qwen2.5-coder:32b",
  "model_type": "local",
  "directory": "~/src/my-project",
  "agent": "coding",
  "terminal": "terminator"
}
```

All fields are optional — anything missing will trigger an interactive prompt (or use defaults).

#### Minimal Config

```json
{
  "model": "qwen2.5-coder:32b",
  "directory": "~/src/project"
}
```

This will prompt for model type, agent, and terminal.

#### Cloud Model Config

```json
{
  "model": "anthropic/claude-3.5-sonnet",
  "model_type": "cloud",
  "directory": "~/src/project",
  "agent": "analyst"
}
```

---

### Config File Location

#### Default Config

The launcher looks for a default config at:

```
~/.config/opencode-launcher/config.json
```

This file is **optional**. If present, it provides baseline defaults.

#### Custom Config Files

You can create project-specific configs anywhere and reference them:

```bash
oc launch --config ~/configs/data-pipeline.json
oc launch --config ./project-config.json
oc launch -c /absolute/path/to/config.json
```

#### Example: Per-Project Configs

```bash
# Create configs for different projects
mkdir -p ~/oc-configs

# Data analysis project
cat > ~/oc-configs/data-analysis.json << 'EOF'
{
  "model": "qwen2.5-coder:32b",
  "model_type": "local",
  "directory": "~/src/data-pipeline",
  "agent": "analyst"
}
EOF

# Web app project
cat > ~/oc-configs/webapp.json << 'EOF'
{
  "model": "anthropic/claude-3.5-sonnet",
  "model_type": "cloud",
  "directory": "~/src/webapp",
  "agent": "coding"
}
EOF

# Launch with one command
oc launch -c ~/oc-configs/data-analysis.json
```

#### Generate Config Interactively

Use `oc init` to create a config file with an interactive wizard:

```bash
# Generate default config
oc init

# Save to a custom location
oc init -o ~/configs/myproject.json
```

---

### Config Fields Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | No | Model name. For local: Ollama model name (e.g., `qwen2.5-coder:32b`). For cloud: provider/model (e.g., `anthropic/claude-3.5-sonnet`). |
| `model_type` | string | No | `"local"` for Ollama models, `"cloud"` for cloud providers. Defaults to interactive prompt. |
| `directory` | string | No | Working directory path. Supports `~` expansion. Must exist (or you'll be prompted to create it). |
| `agent` | string | No | Agent template slug (e.g., `coding`, `analyst`). Must match a `.md` file in the agents directory. |
| `terminal` | string | No | Terminal emulator name (e.g., `terminator`, `gnome-terminal`). Must be installed on the system. |

#### Validation

When loading a config file, the launcher validates:
- **directory** — Checks that the path exists. Warns if it doesn't.
- **agent** — Checks that a matching `.md` template file exists in `~/.config/opencode-launcher/agents/`.

Validation errors are fatal — the launch will abort if the config is invalid.

---

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OC_CONFIG_DIR` | `~/.config/opencode-launcher` | Override the config/data directory. All files (agents, sessions, instances) are stored here. |
| `OLLAMA_API_URL` | `http://localhost:11434` | Ollama API base URL. Change this if Ollama runs on a different host or port. |

#### Examples

```bash
# Use a custom config directory
export OC_CONFIG_DIR="/data/opencode-config"
oc launch

# Connect to remote Ollama
export OLLAMA_API_URL="http://gpu-server:11434"
oc list-models
```

---

### Environment File (.env)

Place a `.env` file in your config directory (`~/.config/opencode-launcher/.env`) to override environment variables:

```bash
# ~/.config/opencode-launcher/.env
OLLAMA_API_URL=http://gpu-server:11434
OC_CONFIG_DIR=/data/opencode-config
```

The `.env` file is loaded on every command and takes precedence over system environment variables but is overridden by explicit CLI flags.

#### Format

- One `KEY=VALUE` per line
- Lines starting with `#` are comments
- Blank lines are ignored
- Values can be quoted (quotes are stripped)

```bash
# Database connection
OLLAMA_API_URL="http://localhost:11434"

# API key (never commit this!)
# OPENAI_API_KEY=sk-...
```

---

### Model Types

#### Local Models (Ollama)

Local models run on your machine via [Ollama](https://ollama.ai). The launcher queries `http://localhost:11434/api/tags` to get available models.

```bash
# List available local models
oc list-models

# Launch with a local model
oc launch -m qwen2.5-coder:32b
oc launch -m deepseek-coder:33b
oc launch -m llama3:8b
```

When `--model-type` is not specified and `-m` is provided, the launcher defaults to **local** unless the model name contains a `/` (which suggests a cloud provider format).

In interactive mode, you're explicitly asked to choose between local and cloud.

#### Cloud Models

Cloud models are served by external providers. The launcher doesn't validate cloud model names — it passes them through to OpenCode.

```bash
# Launch with cloud models
oc launch -m anthropic/claude-3.5-sonnet --model-type cloud -d ~/project
oc launch -m openai/gpt-4o --model-type cloud -d ~/project
```

Cloud models are **not subject** to the local model constraint — you can run different cloud models simultaneously.

---

### Model Constraint

When using local Ollama models, **all running instances must use the same model**.

#### Why?

Ollama loads models into VRAM. If Instance A uses `qwen2.5-coder:32b` and Instance B tries to use `deepseek-coder:33b`, Ollama has to swap the model out and load the new one. This is slow, memory-intensive, and defeats the purpose of having multiple instances.

#### How It Works

```
✅ Instance 1: qwen2.5-coder:32b
   Instance 2: qwen2.5-coder:32b    ← Same model, no problem

❌ Instance 1: qwen2.5-coder:32b
   Instance 2: deepseek-coder:33b   ← REJECTED

✅ Instance 1: local:qwen2.5-coder:32b
   Instance 2: cloud:anthropic/claude-3.5-sonnet  ← Different types, OK
```

#### Workaround

If you need to switch models:

```bash
# Stop all instances using the old model
oc kill-all

# Launch with the new model
oc launch -m deepseek-coder:33b -d ~/project
```

---

### Terminal Preferences

The launcher detects terminal emulators in this priority order:

1. **terminator** (preferred)
2. **gnome-terminal**
3. **konsole**
4. **kitty**
5. **xterm** (fallback)

If only one terminal is detected, it's used automatically without prompting.

You can override the terminal via:
- CLI flag: `oc launch -t konsole`
- Config file: `"terminal": "konsole"`

#### Terminal Launch Behavior

Each terminal is launched differently:

| Terminal | Behavior |
|----------|----------|
| terminator | Opens new tab with `--new-tab` |
| gnome-terminal | Opens new window with `--working-directory` |
| konsole | Opens with `--workdir` |
| kitty | Opens new window with `--working-directory` |
| xterm | Opens with `-e` to execute command |

All terminals run `opencode` followed by `exec bash` to keep the terminal open after OpenCode exits.

---

### Config Precedence

When multiple sources provide the same setting, this precedence applies (highest wins):

```
1. CLI flags          (highest priority)
2. Config file        (--config flag)
3. Default config     (~/.config/opencode-launcher/config.json)
4. Interactive prompt  (fallback for missing fields)
```

#### Example

```bash
# Config file says directory is ~/src/project-a
# CLI flag overrides it to ~/src/project-b
oc launch --config myconfig.json -d ~/src/project-b
# → Uses ~/src/project-b
```

---

### Config Presets

Save and load named configuration presets for quick access:

```bash
# Save current settings as a preset
oc config-save my-project

# Load a preset
oc config-load my-project

# List all presets
oc config-load --list

# Delete a preset
oc config-load my-project --delete
```

Presets are stored in `~/.config/opencode-launcher/presets/` as individual JSON files.

#### Team Sharing

Share presets with teammates via export/import:

```bash
# Export a preset to base64
oc config-save my-project --export

# Import from base64 string
oc config-load --import "eyJtb2RlbCI6ICJxd2Vu..."
```

---

### JSON Schema

The launcher validates config files against this JSON schema:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "model": { "type": "string" },
    "model_type": { "type": "string", "enum": ["local", "cloud"] },
    "directory": { "type": "string" },
    "agent": { "type": "string" },
    "terminal": { "type": "string" }
  },
  "additionalProperties": false
}
```

Validation errors include the field name and a description of what's wrong:

```
❌ Config validation failed:
  • model_type: must be "local" or "cloud", got "ollama"
  • directory: path does not exist: /nonexistent/path
```

---

### Next Steps

- 🤖 [Agents](agents.md) — Create and customize agent templates
- 🔧 [Workflows](workflows.md) — Real-world usage patterns
- 🔥 [Troubleshooting](troubleshooting.md) — When things don't work

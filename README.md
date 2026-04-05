# OpenCode Launcher (`oc`)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

A production-ready CLI tool for launching, managing, and orchestrating multiple [OpenCode](https://opencode.ai) instances from your terminal.

---

## 🤔 Why OpenCode Launcher?

Running a single AI coding assistant is great. Running **multiple instances** across different projects, models, and personas — without losing your mind — is where OpenCode Launcher shines.

Here's what you'd normally deal with **without** it:

- 🔀 Manually opening terminals, navigating to directories, typing out launch commands
- 💥 Accidentally swapping Ollama models mid-session and nuking your VRAM
- 🤷 Forgetting which model/agent combo you used yesterday on that bug-fix branch
- 📂 Juggling config files, environment variables, and terminal settings per project

**OpenCode Launcher eliminates all of that.** One command, one interactive wizard, and you're up and running — whether you're spinning up a local Ollama model for private code or connecting to a cloud model like Claude or GPT for maximum horsepower. It remembers your sessions, enforces sane model constraints, and gives you full visibility into every running instance.

> **TL;DR** — It's the orchestration layer OpenCode deserves: launch, track, resume, and manage AI coding instances like a pro.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [📖 Docs Home](docs/README.md) | Documentation hub & file layout overview |
| [🚀 Getting Started](docs/getting-started.md) | Installation, first launch, core concepts |
| [⌨️ Command Reference](docs/command-reference.md) | All 7 commands with flags, modes & examples |
| [⚙️ Configuration](docs/configuration.md) | Config files, env vars, precedence rules |
| [🤖 Agent Templates](docs/agents.md) | Built-in agents, custom agents, best practices |
| [🔁 Workflows](docs/workflows.md) | Real-world usage patterns & daily driver tips |
| [🔧 Troubleshooting](docs/troubleshooting.md) | Common issues & fixes |
| [❓ FAQ](docs/faq.md) | Frequently asked questions |
| [📝 Changelog](docs/CHANGELOG.md) | Version history |

---

## ✨ Key Features

- **🚀 Multi-Instance Launch** — Spin up 1 or N OpenCode instances in new terminal windows with a single command
- **🤖 Local & Cloud Models** — Seamless support for Ollama local models *and* cloud providers (Claude, GPT, Gemini, etc.)
- **🔒 Smart Model Constraint** — Prevents Ollama model-swapping across instances to protect your VRAM
- **📋 Agent Templates** — 5 built-in personas (Analyst, QA, Coding, General, Technical Writer) + drop-in custom agents
- **💾 Session History** — Automatically saves your last 10 launches for instant resume
- **📊 Instance Tracking** — Real-time status, per-instance stop, or kill-all — stale PIDs cleaned automatically
- **🖥️ Terminal Detection** — Auto-detects gnome-terminal, konsole, kitty, xterm
- **🎨 Interactive TUI** — Beautiful prompts via `questionary` with full CLI-flag fallback
- **📁 Config Files** — JSON configs for repeatable, shareable project setups
- **🔄 Session Resume** — Pick up where you left off, or replay settings in a new directory with `--new_location`

---

## ⚡ Quick Start

```bash
# 1. Install
cd opencode_launcher
bash install.sh

# 2. Launch your first instance (interactive wizard)
oc launch

# 3. Check what's running
oc status
```

That's it. The interactive wizard walks you through model selection, directory, agent, and terminal — no flags needed.

---

## 🎬 Example Workflow

Here's a real-world scenario: you're working on a backend API and a frontend app, using a mix of local and cloud models.

### Local model — backend work
```bash
# Spin up a coding agent with a local Ollama model
oc launch -m qwen2.5-coder:32b -d ~/src/backend-api -a coding
```

### Local model — QA on the same project (same model enforced)
```bash
# Second instance for QA — must use the same local model (constraint enforced)
oc launch -m qwen2.5-coder:32b -d ~/src/backend-api -a qa
```

### ☁️ Cloud model — frontend work
```bash
# Use a cloud model with the explicit --model-type cloud flag
# Interactive selection shows available Zen models
oc launch --model-type cloud -d ~/src/frontend-app -a coding

# Or specify a Zen model directly
oc launch -m claude-sonnet-4-5 --model-type cloud -d ~/src/frontend-app -a coding
```

> 💡 **Tip:** Cloud models are fetched from OpenCode Zen. Get your API key at https://opencode.ai/auth

### Launch from a config file
```bash
# Reusable project config
oc launch --config ~/configs/frontend.json
```

### Resume yesterday's session in a new directory
```bash
oc resume --new_location ~/src/new-feature-branch
```

### Check on everything
```bash
oc status          # See all running instances
oc stop 2          # Stop instance #2
oc kill-all        # Nuclear option — stop everything
```

---

## 🛠️ Installation

### Option 1: Install Script (Recommended)
```bash
cd opencode_launcher
bash install.sh
```

### Option 2: pip
```bash
pip install -e .
```

### Option 3: Run Directly
```bash
python -m opencode_launcher launch
```

### Requirements

- Python 3.10+
- `questionary` (installed automatically)
- A terminal emulator (gnome-terminal, konsole, kitty, or xterm)
- [OpenCode](https://opencode.ai) installed and in PATH
- [Ollama](https://ollama.ai) (for local models only)

---

## 📖 Usage

### Commands

| Command | Description |
|---------|-------------|
| `oc launch` | Launch new OpenCode instance(s) |
| `oc status` | Show running Ollama models (queries Ollama API) |
| `oc stop [id]` | Stop a specific instance (interactive if no ID) |
| `oc kill-all` | Terminate all running instances |
| `oc resume` | Resume from session history |
| `oc list-agents` | List available agent templates |
| `oc list-models` | List available Ollama models |

### Launch Modes

**Interactive (TUI):**
```bash
oc launch
# Walks you through: model source → model → directory → agent → terminal
```

**CLI Flags:**
```bash
# Local model
oc launch -m qwen2.5-coder:32b -d ~/src/project -a coding

# Cloud model (Zen models fetched from opencode.ai)
oc launch -m claude-sonnet-4-5 --model-type cloud -d ~/src/project -a coding

# Multiple instances
oc launch -m qwen2.5-coder:32b -d ~/src/project -n 3
```

**Config File:**
```bash
oc launch --config myproject.json
```

```json
{
  "model": "qwen2.5-coder:32b",
  "model_type": "local",
  "directory": "~/src/project1",
  "agent": "coding",
  "terminal": "terminator"
}
```

**Resume:**
```bash
oc resume                                    # Pick from last 10 sessions
oc resume --new_location ~/src/new_project   # Same settings, new directory
```

### Agent Templates

5 built-in agents in `~/.config/opencode-launcher/agents/`:

| Template | Description |
|----------|-------------|
| `analyst` | Data analysis and insights extraction |
| `qa` | Quality assurance and testing |
| `coding` | Software development |
| `general` | General purpose assistant |
| `technical-writer` | Documentation and technical writing |

**Add your own** — drop a `.md` file with YAML frontmatter into the agents directory:

```markdown
---
name: Security Auditor
description: Security review and vulnerability assessment
temperature: 0.3
---

You are an experienced security auditor...
```

### Model Constraint (Local Only)

All running **local** Ollama instances must use the same model — this prevents constant model swapping that thrashes VRAM:

```
❌ Instance 1: qwen2.5-coder:32b
   Instance 2: deepseek-coder:33b    ← REJECTED

✅ Instance 1: qwen2.5-coder:32b
   Instance 2: qwen2.5-coder:32b    ← OK

✅ Instance 1: qwen2.5-coder:32b (local)
   Instance 2: claude-3.5-sonnet (cloud)  ← OK (constraint is local-only)
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OC_CONFIG_DIR` | `~/.config/opencode-launcher` | Config directory |
| `OLLAMA_API_URL` | `http://localhost:11434` | Ollama API base URL |

---

## 🤝 Contributing

Contributions are welcome! Here's how to get involved:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

Please make sure your code follows the existing style and includes appropriate documentation updates.

---

## 🙏 Acknowledgments

- **[OpenCode](https://opencode.ai)** — The excellent AI coding assistant that this tool orchestrates. OpenCode Launcher exists to make the OpenCode experience even better when working across multiple projects and models.
- **[Ollama](https://ollama.ai)** — For making local LLM inference accessible and fast.
- **[questionary](https://github.com/tmbo/questionary)** — For the beautiful interactive terminal prompts.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 csb (unclebucklarson)

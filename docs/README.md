# OpenCode Launcher Documentation

> Your one-stop guide to launching, managing, and wrangling OpenCode instances like a caffeinated sysadmin.

```
  ___                    ____          _
 / _ \ _ __   ___ _ __  / ___|___   __| | ___
| | | | '_ \ / _ \ '_ \| |   / _ \ / _` |/ _ \
| |_| | |_) |  __/ | | | |__| (_) | (_| |  __/
 \___/| .__/ \___|_| |_|\____\___/ \__,_|\___|   Launcher
      |_|
```

---

### What is OpenCode Launcher?

OpenCode Launcher (`oc`) is a CLI tool that lets you spin up, track, and manage multiple [OpenCode](https://opencode.ai) instances from your terminal. Think of it as a mission control for your AI coding sessions — pick a model, pick an agent, point it at a directory, and go.

#### Key Features

- **🚀 Launch instances** in dedicated terminal windows
- **🤖 Model selection** — local Ollama models or cloud providers
- **🔒 Model constraint** — prevents VRAM thrashing by enforcing one local model at a time
- **📋 Agent templates** — 5 built-in personas (Analyst, QA, Coding, General, Technical Writer)
- **💾 Session history** — remembers your last 10 sessions for quick resume
- **📊 Instance tracking** — see what's running, stop one, or nuke them all
- **🖥️ Terminal detection** — auto-detects your terminal emulator
- **🎨 Interactive TUI** — pretty prompts with CLI fallback
- **📁 Config files** — JSON configs for repeatable project setups

---

### Quick Start

```bash
# 1. Install
cd opencode_launcher
bash install.sh

# 2. Launch interactively (the wizard walks you through everything)
oc launch

# 3. Check what's running
oc status
```

That's it. You're dangerous now. For the full story, keep reading.

---

### Documentation Index

| Document | What's Inside |
|----------|---------------|
| [Getting Started](getting-started.md) | Installation, first-time setup, your first launch |
| [Command Reference](command-reference.md) | Every command, flag, and option in detail |
| [Configuration](configuration.md) | Config files, environment variables, model types |
| [Agents](agents.md) | Agent templates — built-in, custom, and how they work |
| [Workflows](workflows.md) | Real-world usage patterns and best practices |
| [Troubleshooting](troubleshooting.md) | When things go sideways |
| [FAQ](faq.md) | Frequently asked questions and pro tips |
| [Changelog](CHANGELOG.md) | Version history |

---

### System Requirements

| Requirement | Details |
|---|---|
| Python | 3.10+ |
| Terminal | gnome-terminal, konsole, kitty, or xterm |
| OpenCode | Installed and in PATH ([opencode.ai](https://opencode.ai)) |
| Ollama | Required for local models ([ollama.ai](https://ollama.ai)) |
| OS | Linux (terminal detection relies on Linux emulators) |

---

### File Layout

```
opencode_launcher/                  # Source code
├── cli.py                          # CLI entry point & commands
├── config.py                       # Config file loading/validation
├── models.py                       # Ollama API integration
├── terminals.py                    # Terminal detection & launching
├── sessions.py                     # Session history management
├── instances.py                    # Running instance tracking
├── agents.py                       # Agent template parsing
├── constants.py                    # Paths, URLs, terminal preferences
├── install.sh                      # Installer script
├── setup.py                        # Python package setup
└── docs/                           # 📍 You are here

~/.config/opencode-launcher/        # Runtime data
├── agents/                         # Agent template files
│   ├── analyst.md
│   ├── coding.md
│   ├── general.md
│   ├── qa.md
│   └── technical-writer.md
├── sessions.json                   # Last 10 session history
├── instances.json                  # Currently running instances (PID-tracked)
├── stopped_instances.json          # Stopped instances for restart
├── config.json                     # Default config (optional)
├── .env                            # Environment overrides (optional)
├── presets/                        # Named config presets
└── logs/                           # Instance output logs
```

---

### Contributing

Got a feature idea or found a bug? Open an issue or submit a PR. Agent templates are especially welcome — the more personas, the merrier.

---

*Built with ☕ and questionable amounts of terminal tabs.*

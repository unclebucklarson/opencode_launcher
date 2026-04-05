# Getting Started

From zero to launching OpenCode instances in under 5 minutes.

---

### Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [First-Time Setup](#first-time-setup)
- [Your First Launch](#your-first-launch)
- [Basic Concepts](#basic-concepts)

---

### Prerequisites

Before installing, make sure you have:

1. **Python 3.10+** — Check with `python3 --version`
2. **A supported terminal emulator** — At least one of:
   - `terminator` (recommended)
   - `gnome-terminal`
   - `konsole`
   - `xterm`
3. **OpenCode** — Installed and available in your PATH. Get it from [opencode.ai](https://opencode.ai).
4. **Ollama** *(optional, for local models)* — Get it from [ollama.ai](https://ollama.ai). If you only plan to use cloud models, you can skip this.

---

### Installation

#### Option 1: Install Script (Recommended)

```bash
cd opencode_launcher
bash install.sh
```

The install script will:
- Verify your Python version
- Install the `questionary` dependency
- Create the config directory (`~/.config/opencode-launcher/`)
- Set up the `oc` command in `~/.local/bin/`

#### Option 2: pip install

```bash
cd opencode_launcher
pip install -e .
```

This installs the package in editable mode and creates the `oc` console script.

#### Option 3: Run Directly

No installation needed — just run the module:

```bash
python3 -m opencode_launcher.cli launch
```

#### Verify Installation

```bash
oc --version
# oc 1.0.0

oc --help
# Shows the banner and all available commands
```

If `oc` isn't found, add pip's bin directory to your PATH:

```bash
export PATH="${HOME}/.local/bin:${PATH}"
```

Add that line to your `~/.bashrc` or `~/.zshrc` to make it permanent.

---

### First-Time Setup

After installation, the config directory is created automatically at `~/.config/opencode-launcher/`. It contains:

```
~/.config/opencode-launcher/
├── agents/             # Agent template markdown files
│   ├── analyst.md
│   ├── coding.md
│   ├── general.md
│   ├── qa.md
│   └── technical-writer.md
├── sessions.json       # Created on first launch
├── instances.json      # Created on first launch
└── config.json         # Optional default config
```

#### Setting Up Ollama (for local models)

If you want to use local models:

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Start the Ollama service
ollama serve

# Pull a model
ollama pull qwen2.5-coder:32b

# Verify it's available
oc list-models
```

---

### Your First Launch

The easiest way to start is the interactive wizard:

```bash
oc launch
```

The wizard walks you through 4 steps:

#### Step 1: Model Source
```
? Model source?
❯ local (Ollama)
  cloud (manual entry)
```

Choose **local** to pick from your Ollama models, or **cloud** to type in a provider/model string.

#### Step 2: Model Selection

For local:
```
? Select Ollama model:
❯ qwen2.5-coder:32b
  llama3:8b
  deepseek-coder:33b
```

For cloud:
```
? Enter cloud model name: anthropic/claude-3.5-sonnet
```

#### Step 3: Working Directory
```
? Working directory: [/home/you/current/dir]
```

Press Enter to use the current directory, or type a path. If the directory doesn't exist, you'll be asked whether to create it.

#### Step 4: Agent Template
```
? Select agent template:
❯ analyst         - Data analysis and insights extraction
  coding          - Software development, architecture, and implementation agent
  general         - General purpose assistant
  qa              - Quality assurance and testing
  technical-writer - Documentation and technical writing
  (none)          - No agent file
```

Pick an agent persona or select **(none)** to launch without one.

#### Step 5: Terminal (if multiple available)
```
? Select terminal emulator:
❯ terminator
  gnome-terminal
```

If only one terminal is detected, it's used automatically.

#### Result
```
🚀 Launching 1 instance(s)...
   Model:     local:qwen2.5-coder:32b
   Directory: /home/you/src/project
   Agent:     coding
   Terminal:  terminator

  ✅ Instance a3f7b2c1 started (PID 12345)

✨ Done! Use 'oc status' to check running instances.
```

A new terminal window opens with OpenCode running in your project directory. 🎉

---

### Basic Concepts

#### Instances
Each launch creates an **instance** — a terminal window running OpenCode. Instances are tracked by PID and can be monitored with `oc status`, stopped individually with `oc stop`, or nuked collectively with `oc kill-all`.

#### Sessions
Every launch is recorded as a **session**. The launcher remembers your last 10 sessions, so you can quickly resume previous work with `oc resume`. Sessions store the model, directory, agent, and terminal you used.

#### Agents
**Agent templates** are Markdown files with YAML frontmatter that define a persona for OpenCode. They set the system prompt, temperature, and behavioral guidelines. See the [Agents](agents.md) doc for details.

#### Model Types
- **Local** — Models served by Ollama on your machine. Subject to the [single-model constraint](configuration.md#model-constraint).
- **Cloud** — Models from providers like Anthropic, OpenAI, etc. No constraints between instances.

#### The Single-Model Constraint
When using local Ollama models, **all running instances must use the same model**. This prevents Ollama from constantly swapping models in/out of VRAM, which is slow and painful. Cloud models are exempt from this constraint.

---

### Next Steps

- 📖 [Command Reference](command-reference.md) — All commands and flags
- ⚙️ [Configuration](configuration.md) — Config files and environment variables
- 🤖 [Agents](agents.md) — Customize your agent personas
- 🔧 [Workflows](workflows.md) — Real-world usage patterns

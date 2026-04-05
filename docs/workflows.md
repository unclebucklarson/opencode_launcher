# Workflows & Best Practices

Real-world patterns for getting the most out of OpenCode Launcher.

---

### Table of Contents

- [Single Project, Single Instance](#single-project-single-instance)
- [Multi-Instance Same Project](#multi-instance-same-project)
- [Multi-Project Setup](#multi-project-setup)
- [Cloud + Local Mixing](#cloud--local-mixing)
- [Session Resume Workflows](#session-resume-workflows)
- [Config File Workflows](#config-file-workflows)
- [Daily Driver Workflow](#daily-driver-workflow)
- [Best Practices](#best-practices)

---

### Single Project, Single Instance

The simplest workflow — one project, one AI helper.

```bash
# Morning: start your coding session
oc launch -m qwen2.5-coder:32b -d ~/src/my-app -a coding

# Check it's running
oc status

# End of day: clean up
oc kill-all
```

---

### Multi-Instance Same Project

Need multiple AI sessions on the same codebase? Maybe one for coding and one for testing.

```bash
# Launch a coding instance
oc launch -m qwen2.5-coder:32b -d ~/src/my-app -a coding

# Launch a QA instance (same model — constraint enforced)
oc launch -m qwen2.5-coder:32b -d ~/src/my-app -a qa

# Or launch 3 coding instances at once
oc launch -m qwen2.5-coder:32b -d ~/src/my-app -a coding -n 3
```

> **Remember:** All local instances must use the same Ollama model. The launcher enforces this automatically.

---

### Multi-Project Setup

Working across multiple codebases? Each gets its own terminal.

```bash
# Frontend project
oc launch -m qwen2.5-coder:32b -d ~/src/frontend -a coding

# Backend project (same model required)
oc launch -m qwen2.5-coder:32b -d ~/src/backend -a coding

# Data pipeline (analyst persona)
oc launch -m qwen2.5-coder:32b -d ~/src/data-pipeline -a analyst

# Check everything
oc status
```

---

### Cloud + Local Mixing

Cloud and local models have separate constraint spaces. You can run both simultaneously.

```bash
# Local instance for fast iteration
oc launch -m qwen2.5-coder:32b -d ~/src/project -a coding

# Cloud instance for complex reasoning tasks
oc launch -m anthropic/claude-3.5-sonnet --model-type cloud -d ~/src/project -a analyst

# Another cloud instance (different cloud model — totally fine)
oc launch -m openai/gpt-4o --model-type cloud -d ~/src/project -a general
```

#### When to Use Each

| Use Case | Recommendation |
|----------|----------------|
| Quick code edits & iteration | Local (low latency) |
| Complex architecture decisions | Cloud (stronger reasoning) |
| Large codebase analysis | Cloud (larger context) |
| Offline work | Local (no internet needed) |
| Cost-sensitive tasks | Local (free after model download) |
| Specialized tasks (vision, etc.) | Cloud (model variety) |

---

### Session Resume Workflows

Sessions are your quick-launch memory. The launcher remembers your last 10.

#### Basic Resume

```bash
# End of yesterday — you close everything
# Start of today:
oc resume
# Pick yesterday's session → same model, same dir, same agent
```

#### Resume to a Different Directory

Have a standard setup (model + agent) that you reuse across projects?

```bash
# Yesterday you worked on project-a with coding agent + qwen2.5
# Today you want the same setup but for project-b
oc resume --new_location ~/src/project-b
```

This keeps the model and agent from the selected session but redirects to the new directory.

#### Resume Pattern: Template Sessions

Launch once with your ideal settings, then resume forever:

```bash
# First time: set up the perfect session
oc launch -m qwen2.5-coder:32b -a coding -d ~/src/any-project

# Every subsequent time: just resume + redirect
oc resume --new_location ~/src/todays-project
oc resume --new_location ~/src/another-project
```

---

### Config File Workflows

#### Per-Project Config Files

Store a config in each project:

```bash
# ~/src/my-app/.opencode.json
{
  "model": "qwen2.5-coder:32b",
  "model_type": "local",
  "directory": ".",
  "agent": "coding"
}

# Launch from project directory
cd ~/src/my-app
oc launch --config .opencode.json
```

#### Shared Config Library

```bash
mkdir -p ~/oc-configs

# Create role-specific configs
echo '{"model":"qwen2.5-coder:32b","model_type":"local","agent":"coding"}' > ~/oc-configs/coder.json
echo '{"model":"qwen2.5-coder:32b","model_type":"local","agent":"analyst"}' > ~/oc-configs/analyst.json
echo '{"model":"anthropic/claude-3.5-sonnet","model_type":"cloud","agent":"qa"}' > ~/oc-configs/qa-cloud.json

# Launch with config + directory override
oc launch -c ~/oc-configs/coder.json -d ~/src/my-project
```

#### Shell Aliases

For the truly lazy (we respect it):

```bash
# Add to ~/.bashrc or ~/.zshrc
alias oc-code='oc launch -c ~/oc-configs/coder.json -d'
alias oc-analyze='oc launch -c ~/oc-configs/analyst.json -d'
alias oc-qa='oc launch -c ~/oc-configs/qa-cloud.json -d'

# Usage
oc-code ~/src/my-project
oc-analyze ~/data/pipeline
oc-qa ~/src/critical-service
```

---

### Daily Driver Workflow

A recommended daily workflow for regular use:

```bash
# 🌅 Morning: Start fresh
oc list-models                      # Make sure Ollama is running
oc launch -m qwen2.5-coder:32b \    # Launch your main session
  -d ~/src/main-project -a coding

# 🏗️ Working: Add instances as needed
oc launch -m qwen2.5-coder:32b \    # Second instance for testing
  -d ~/src/main-project -a qa
oc status                            # Check your fleet

# 🔄 Context switch: Stop one, start another
oc stop                              # Pick the QA instance
oc launch -m qwen2.5-coder:32b \    # Start a docs instance
  -d ~/src/main-project -a technical-writer

# 🌙 End of day: Clean up
oc kill-all

# 🌅 Next morning: Resume where you left off
oc resume
```

---

### Best Practices

#### 1. Use the Right Agent for the Job

Don't use `general` for everything. A focused agent produces better results:
- Writing code? → `coding`
- Reviewing/testing? → `qa`
- Writing docs? → `technical-writer`
- Analyzing data? → `analyst`

#### 2. One Model, Many Instances

Instead of switching models, run multiple instances of the same model with different agents. The model constraint exists for a reason — VRAM swapping kills performance.

#### 3. Create Project-Specific Configs

If you revisit a project often, create a config file. It's faster than typing flags every time and ensures consistency.

#### 4. Clean Up Regularly

```bash
# Quick status check
oc status

# Stale instances are auto-cleaned, but kill-all is your friend
oc kill-all
```

#### 5. Use Resume for Repetitive Setups

`oc resume --new_location` is your best friend for applying a known-good setup to different directories.

#### 6. Monitor with `oc status`

Keep an eye on your running instances. The status command also auto-cleans stale entries (terminals you closed manually).

#### 7. Verbose Mode for Debugging

If something isn't working, add `-v`:

```bash
oc -v launch -m qwen2.5-coder:32b -d ~/project
```

This shows debug logs including the actual terminal launch commands.

---

### Next Steps

- 🔥 [Troubleshooting](troubleshooting.md) — When things go wrong
- ❓ [FAQ](faq.md) — Quick answers to common questions

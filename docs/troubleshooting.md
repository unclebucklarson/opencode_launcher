# Troubleshooting

When things go sideways, this is your field guide.

---

### Table of Contents

- [Ollama Connection Problems](#ollama-connection-problems)
- [Terminal Detection Issues](#terminal-detection-issues)
- [Model Constraint Errors](#model-constraint-errors)
- [Stale Instance Cleanup](#stale-instance-cleanup)
- [Command Not Found](#command-not-found)
- [Agent Template Issues](#agent-template-issues)
- [Config File Errors](#config-file-errors)
- [General Debugging](#general-debugging)

---

### Ollama Connection Problems

#### "Ollama is not running!"

**Cause:** The launcher can't reach Ollama's API at `http://localhost:11434`.

**Solutions:**

```bash
# 1. Start Ollama
ollama serve

# 2. Check if it's running
curl http://localhost:11434/api/tags

# 3. If Ollama is on a different host/port
export OLLAMA_API_URL="http://your-server:11434"
oc list-models
```

#### "No models found in Ollama"

**Cause:** Ollama is running but no models are pulled.

**Solution:**

```bash
# Pull a model
ollama pull qwen2.5-coder:32b

# Verify
ollama list
oc list-models
```

#### Timeout When Listing Models

**Cause:** Ollama is responding slowly (possibly loading a model).

**Solution:** Wait for the current model operation to finish, then try again. The launcher has a 10-second timeout for model listing.

---

### Terminal Detection Issues

#### "No supported terminal emulators found!"

**Cause:** None of the supported terminals (terminator, gnome-terminal, konsole, xterm) are installed or in PATH.

**Solutions:**

```bash
# Install terminator (recommended)
sudo apt install terminator

# Or gnome-terminal
sudo apt install gnome-terminal

# Or xterm (lightweight fallback)
sudo apt install xterm

# Verify detection
which terminator gnome-terminal konsole xterm
```

#### Terminal Opens But Closes Immediately

**Cause:** The OpenCode command failed, and the terminal exited.

**Solutions:**

1. **Check OpenCode is installed:**
   ```bash
   which opencode
   opencode --version
   ```

2. **Test manually:**
   ```bash
   # Open a terminal and run:
   cd ~/your/project
   opencode
   ```

3. **Use verbose mode:**
   ```bash
   oc -v launch -m qwen2.5-coder:32b -d ~/project
   # Check the launched command in debug output
   ```

#### Wrong Terminal Opens

**Cause:** Multiple terminals detected, and the auto-selection picked the wrong one.

**Solution:** Specify the terminal explicitly:

```bash
oc launch -t terminator -m qwen2.5-coder:32b -d ~/project
```

Or set it in your config file:
```json
{"terminal": "terminator"}
```

---

### Model Constraint Errors

#### "All local instances must use the same model"

**Cause:** You're trying to launch a local instance with a different model than what's already running.

**Solutions:**

```bash
# Option 1: Use the same model as running instances
oc status  # Check what model is running
oc launch -m <same-model> -d ~/project

# Option 2: Stop all instances and switch models
oc kill-all
oc launch -m <new-model> -d ~/project

# Option 3: Use a cloud model instead (no constraint)
oc launch -m anthropic/claude-3.5-sonnet --model-type cloud -d ~/project
```

#### "Multiple local models detected"

**Cause:** The instance registry somehow has entries with different local models. This shouldn't happen under normal use.

**Solution:**

```bash
# Clean slate
oc kill-all

# If that doesn't work, manually clear the registry
rm ~/.config/opencode-launcher/instances.json
oc launch
```

---

### Stale Instance Cleanup

#### Instance Shows Running But Terminal Is Closed

**Cause:** You closed the terminal window manually, but the PID entry still exists in the registry.

**Solution:** The launcher auto-cleans stale PIDs on `oc status`:

```bash
oc status
# Stale entries are automatically removed
```

If auto-cleanup doesn't work:

```bash
# Manual cleanup
oc kill-all

# Nuclear option
rm ~/.config/opencode-launcher/instances.json
```

#### Lots of Stale Entries

**Cause:** Frequently closing terminals without using `oc stop` or `oc kill-all`.

**Best practice:** Use `oc stop` or `oc kill-all` instead of closing terminal windows directly. But stale entries are harmless — they get cleaned up automatically.

---

### Command Not Found

#### "`oc` command not found"

**Cause:** The `oc` script isn't in your PATH.

**Solutions:**

```bash
# 1. Add ~/.local/bin to PATH
export PATH="${HOME}/.local/bin:${PATH}"

# 2. Make it permanent
echo 'export PATH="${HOME}/.local/bin:${PATH}"' >> ~/.bashrc
source ~/.bashrc

# 3. Verify
which oc
oc --version
```

**Alternative:** Run directly without installation:

```bash
python3 -m opencode_launcher.cli launch
```

#### "`opencode` command not found"

**Cause:** OpenCode itself isn't installed or isn't in PATH.

**Solution:** Install OpenCode following the instructions at [opencode.ai](https://opencode.ai) and ensure it's available in your PATH.

---

### Agent Template Issues

#### "Agent template not found"

**Cause:** The specified agent slug doesn't match any `.md` file in the agents directory.

**Solutions:**

```bash
# List available agents
oc list-agents

# Check files in agents directory
ls ~/.config/opencode-launcher/agents/

# Slugs are filenames without .md
# "coding" → coding.md
# "my-agent" → my-agent.md
```

#### Custom Agent Not Appearing

**Cause:** The file isn't in the right location or has the wrong extension.

**Checklist:**
- File is in `~/.config/opencode-launcher/agents/`
- File has `.md` extension
- File has valid YAML frontmatter (starts with `---`)

```bash
# Verify
cat ~/.config/opencode-launcher/agents/your-agent.md
# Should start with:
# ---
# name: ...
# description: ...
# temperature: ...
# ---
```

#### Agent Frontmatter Parse Error

**Cause:** Invalid YAML in the frontmatter.

**Common mistakes:**
- Missing `---` delimiters
- Colon in value without quotes (e.g., `description: This: is broken`)
- Indentation issues

**Fix:**
```markdown
---
name: My Agent
description: A simple description without special characters
temperature: 0.5
---
```

---

### Config File Errors

#### "Could not load config"

**Cause:** The config file doesn't exist, isn't valid JSON, or has a read error.

**Solutions:**

```bash
# Check the file exists
ls -la your-config.json

# Validate JSON
python3 -m json.tool your-config.json

# Common issue: trailing commas
# ❌ {"model": "qwen2.5-coder:32b",}  ← trailing comma
# ✅ {"model": "qwen2.5-coder:32b"}
```

#### Config Validation Warnings

**Cause:** The config references a directory that doesn't exist or an agent that isn't installed.

**Note:** These are warnings, not errors. The launcher will still work — it'll prompt for corrections interactively.

---

### General Debugging

#### Enable Verbose Mode

```bash
oc -v launch -m qwen2.5-coder:32b -d ~/project
```

This shows:
- Config loading details
- Model constraint checks
- Terminal launch commands
- Session/instance tracking operations

#### Check the Data Files

```bash
# Session history
cat ~/.config/opencode-launcher/sessions.json | python3 -m json.tool

# Instance registry
cat ~/.config/opencode-launcher/instances.json | python3 -m json.tool
```

#### Reset Everything

If all else fails, a clean slate:

```bash
# Kill all instances
oc kill-all

# Reset data files (keeps agents)
rm ~/.config/opencode-launcher/sessions.json
rm ~/.config/opencode-launcher/instances.json

# Full reset (including agents)
rm -rf ~/.config/opencode-launcher
bash install.sh  # Re-install
```

---

### Still Stuck?

If none of the above helps:

1. Run with `-v` flag and check the output carefully
2. Check that all prerequisites are installed (`python3`, `opencode`, `ollama`, terminal emulator)
3. Try running OpenCode directly in a terminal to isolate the issue
4. Check file permissions on `~/.config/opencode-launcher/`

---

### Next Steps

- ❓ [FAQ](faq.md) — Quick answers to common questions
- 📖 [Command Reference](command-reference.md) — Double-check your syntax

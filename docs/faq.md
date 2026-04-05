# Frequently Asked Questions

Quick answers to the questions you didn't know you had.

---

### Table of Contents

- [General](#general)
- [Models](#models)
- [Agents](#agents)
- [Instances & Sessions](#instances--sessions)
- [Tips & Tricks](#tips--tricks)
- [Performance](#performance)

---

### General

#### Q: What exactly is OpenCode Launcher?

**A:** It's a CLI tool (`oc`) that manages OpenCode instances. Think of it as a task manager for AI coding sessions — it handles launching instances in separate terminals, tracking what's running, and managing model/agent configurations. OpenCode itself is the AI coding tool; the launcher just orchestrates it.

#### Q: Does it work on macOS/Windows?

**A:** Currently, the terminal detection is Linux-specific (terminator, gnome-terminal, konsole, xterm). macOS and Windows aren't supported out of the box. PRs welcome!

#### Q: Can I use it without Ollama?

**A:** Yes! Use cloud models with `--model-type cloud`. You'll need to specify the model manually (e.g., `anthropic/claude-3.5-sonnet`), and the `list-models` command won't work, but launching and managing instances works fine.

#### Q: Is `questionary` required?

**A:** It's strongly recommended for the nice TUI prompts. If it's not installed, the launcher falls back to basic `input()` prompts. Everything works, it's just less pretty.

---

### Models

#### Q: Why can't I use different local models for different instances?

**A:** The single-model constraint prevents Ollama from constantly loading/unloading models from VRAM. Every model swap takes time and can cause OOM errors. By enforcing one model at a time, your instances share the already-loaded model efficiently.

#### Q: Can I mix local and cloud models?

**A:** Absolutely. Cloud models don't interact with Ollama at all, so they're exempt from the local model constraint. Run `qwen2.5-coder:32b` locally alongside `anthropic/claude-3.5-sonnet` in the cloud — no problem.

#### Q: How do I switch to a different local model?

**A:** Stop all running local instances first:

```bash
oc kill-all
oc launch -m <new-model> -d ~/project
```

#### Q: Where does the model list come from?

**A:** `oc list-models` queries Ollama's API at `http://localhost:11434/api/tags`. It shows whatever models you've pulled with `ollama pull`. Change the API URL with the `OLLAMA_API_URL` environment variable if Ollama is running elsewhere.

#### Q: What model names work for cloud?

**A:** Any string you pass is forwarded to OpenCode as-is. Common formats:
- `anthropic/claude-3.5-sonnet`
- `openai/gpt-4o`
- `google/gemini-pro`

The launcher doesn't validate cloud model names — that's between you and OpenCode.

---

### Agents

#### Q: Do I have to use an agent?

**A:** Nope. Select `(none)` in the wizard or omit the `-a` flag. OpenCode will use its default behavior.

#### Q: Can I edit built-in agents?

**A:** Yes. They're just Markdown files in `~/.config/opencode-launcher/agents/`. Edit them freely — changes take effect on the next launch.

#### Q: How do I create a new agent?

**A:** Create a `.md` file in `~/.config/opencode-launcher/agents/` with YAML frontmatter:

```markdown
---
name: My Custom Agent
description: Does cool things
temperature: 0.5
---

Your system prompt here.
```

See [Agents](agents.md) for detailed instructions and examples.

#### Q: What's the temperature do?

**A:** It controls randomness in the model's output:
- **0.0–0.3:** Very focused and deterministic. Good for code, analysis, factual tasks.
- **0.4–0.6:** Balanced. Good for general tasks.
- **0.7–1.0:** More creative and varied. Good for brainstorming and content.

---

### Instances & Sessions

#### Q: What happens when I close a terminal window?

**A:** The instance entry becomes "stale" — the PID no longer exists. Next time you run `oc status`, stale entries are automatically cleaned up. No harm done.

#### Q: How many instances can I run?

**A:** As many as your system can handle. The launcher doesn't impose a limit. Your bottleneck is typically VRAM (for local models) or API rate limits (for cloud).

#### Q: Can I resume a session from yesterday?

**A:** Yes, if it's within the last 10 sessions. The launcher keeps a rolling history:

```bash
oc resume
# Pick from the list
```

#### Q: What does `--new_location` do with resume?

**A:** It keeps all settings (model, model type, agent, terminal) from the selected session but changes the working directory:

```bash
# Resume session #3 but work in a different directory
oc resume --new_location ~/src/new-project
```

#### Q: Where is session data stored?

**A:** In `~/.config/opencode-launcher/sessions.json`. It's a plain JSON file containing the last 10 sessions with timestamps, model info, directory, agent, and terminal.

---

### Tips & Tricks

#### Set up shell aliases for common configs

```bash
alias occ='oc launch -m qwen2.5-coder:32b -a coding -d'
alias ocq='oc launch -m qwen2.5-coder:32b -a qa -d'
alias oca='oc launch -m qwen2.5-coder:32b -a analyst -d'

# Usage:
occ ~/src/my-project
ocq ~/src/my-project
```

#### Quick launch + resume pattern

Launch once, resume forever:
```bash
# Day 1: Full setup
oc launch -m qwen2.5-coder:32b -a coding -d ~/src/project

# Day 2+: Just resume
oc resume
```

#### Check what model instances are using

```bash
oc status | grep Model
```

#### Nuke and restart when things get weird

```bash
oc kill-all && oc launch
```

---

### Performance

#### Q: Does running multiple instances use more VRAM?

**A:** Not significantly for local models — Ollama shares the loaded model across concurrent requests. The model is loaded once in VRAM, regardless of how many instances are querying it.

#### Q: How much memory does the launcher itself use?

**A:** Negligible. The launcher is a thin Python CLI — it spawns terminal processes and exits. The running instances are independent terminal + OpenCode processes.

#### Q: Will many instances slow down responses?

**A:** For local models: yes, if all instances are making simultaneous requests. Ollama processes requests sequentially (or in limited parallelism depending on config). For cloud models: depends on your API rate limits.

#### Q: Can I connect to a remote Ollama server?

**A:** Yes:

```bash
export OLLAMA_API_URL="http://gpu-server:11434"
oc list-models
oc launch
```

This is great for shared GPU servers. Note that the model constraint still applies — all local instances on your launcher must use the same model.

---

### Next Steps

- 📖 [Getting Started](getting-started.md) — If you haven't set up yet
- 🔥 [Troubleshooting](troubleshooting.md) — For specific error messages
- 🔧 [Workflows](workflows.md) — Real-world usage patterns

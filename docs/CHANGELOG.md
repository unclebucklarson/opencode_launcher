# Changelog

All notable changes to OpenCode Launcher will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-04-05

### Added

- **CLI tool (`oc`)** with 7 commands: `launch`, `status`, `stop`, `kill-all`, `resume`, `list-agents`, `list-models`
- **Interactive TUI** using `questionary` with graceful fallback to basic prompts
- **Three launch modes:** interactive wizard, CLI flags, and JSON config files
- **Local model support** via Ollama API integration
  - Auto-detection of available models
  - Single-model constraint enforcement for VRAM efficiency
- **Cloud model support** with manual model name entry
- **5 built-in agent templates:**
  - `analyst` — Data analysis and insights
  - `coding` — Software development
  - `general` — General purpose
  - `qa` — Quality assurance and testing
  - `technical-writer` — Documentation
- **Custom agent support** — Drop `.md` files with YAML frontmatter into the agents directory
- **Session management** — Tracks last 10 sessions for quick resume
- **`--new_location` resume flag** — Reuse session settings with a different directory
- **Instance tracking** — Monitor, stop, or kill running instances
- **Stale instance cleanup** — Auto-removes dead PIDs from registry
- **Terminal detection** — Supports terminator, gnome-terminal, konsole, xterm
- **Multi-instance launch** — Spin up N instances with `-n` flag
- **Config file support** — JSON configs with validation
- **Environment variables** — `OC_CONFIG_DIR` and `OLLAMA_API_URL` overrides
- **Install script** (`install.sh`) with PATH-safe wrapper
- **Comprehensive documentation** in `docs/` directory

---

## [Unreleased]

*Nothing yet — stay tuned!*

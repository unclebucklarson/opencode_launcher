# Copyright (c) 2026 csb (unclebucklarson)
# Licensed under the MIT License - see LICENSE file for details

"""Agent template management."""

import logging
from pathlib import Path

from .constants import AGENTS_DIR

log = logging.getLogger(__name__)

REQUIRED_FIELDS = ["name", "description"]


def list_agents() -> list[dict]:
    """List all available agent templates with their metadata."""
    agents = []
    if not AGENTS_DIR.exists():
        return agents
    for f in sorted(AGENTS_DIR.glob("*.md")):
        meta = parse_agent_frontmatter(f)
        warnings = validate_agent(meta, f)
        agents.append(
            {
                "slug": f.stem,
                "file": str(f),
                "name": meta.get("name", f.stem),
                "description": meta.get("description", ""),
                "temperature": meta.get("temperature", 0.5),
                "warnings": warnings,
            }
        )
    return agents


def get_agent_slugs() -> list[str]:
    """Get list of agent slug names."""
    return [a["slug"] for a in list_agents()]


def get_agent_path(slug: str) -> Path | None:
    """Get the file path for an agent by slug."""
    path = AGENTS_DIR / f"{slug}.md"
    return path if path.exists() else None


def parse_agent_frontmatter(filepath: Path) -> dict:
    """Parse YAML frontmatter from a markdown agent file."""
    try:
        text = filepath.read_text()
    except IOError:
        return {}

    if not text.startswith("---"):
        return {}

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}

    frontmatter = parts[1].strip()
    meta = {}
    for line in frontmatter.split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            value = value.strip()
            # Strip surrounding quotes if present
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            # Try to parse numbers
            try:
                value = float(value)
                if value == int(value):
                    value = int(value)
            except (ValueError, TypeError):
                pass
            meta[key.strip()] = value
    return meta


def validate_agent(meta: dict, filepath: Path) -> list[str]:
    """Validate agent frontmatter. Returns list of warning messages."""
    warnings = []
    for field in REQUIRED_FIELDS:
        if field not in meta:
            warnings.append(f"Missing required field: '{field}' in {filepath.name}")
    temp = meta.get("temperature")
    if temp is not None:
        try:
            t = float(temp)
            if t < 0 or t > 2:
                warnings.append(
                    f"Temperature {t} out of range [0, 2] in {filepath.name}"
                )
        except (ValueError, TypeError):
            warnings.append(f"Invalid temperature value '{temp}' in {filepath.name}")
    return warnings


def format_agent(agent: dict) -> str:
    """Format an agent for display."""
    return f"  {agent['slug']:20s} {agent['name']:25s} {agent['description']}"

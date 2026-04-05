# Copyright (c) 2026 csb (unclebucklarson)
# Licensed under the MIT License - see LICENSE file for details

"""Agent template management."""
import logging
from pathlib import Path
from typing import Optional

from .constants import AGENTS_DIR

log = logging.getLogger(__name__)


def list_agents() -> list[dict]:
    """List all available agent templates with their metadata."""
    agents = []
    if not AGENTS_DIR.exists():
        return agents
    for f in sorted(AGENTS_DIR.glob("*.md")):
        meta = parse_agent_frontmatter(f)
        agents.append({
            "slug": f.stem,
            "file": str(f),
            "name": meta.get("name", f.stem),
            "description": meta.get("description", ""),
            "temperature": meta.get("temperature", 0.5),
        })
    return agents


def get_agent_slugs() -> list[str]:
    """Get list of agent slug names."""
    return [a["slug"] for a in list_agents()]


def get_agent_path(slug: str) -> Optional[Path]:
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
            # Try to parse numbers
            try:
                value = float(value)
                if value == int(value):
                    value = int(value)
            except (ValueError, TypeError):
                pass
            meta[key.strip()] = value
    return meta


def format_agent(agent: dict) -> str:
    """Format an agent for display."""
    return f"  {agent['slug']:20s} {agent['name']:25s} {agent['description']}"

"""Load persona definitions from kb/personas/."""
import logging
from pathlib import Path

import yaml

from intel_engine.schemas.persona import PersonaDefinition, PersonaStatus

logger = logging.getLogger(__name__)


def load_personas(kb_root: Path) -> list[PersonaDefinition]:
    base = kb_root / "personas"
    if not base.exists():
        return []
    out: list[PersonaDefinition] = []
    for path in base.rglob("*.md"):
        if path.name.startswith("_"):
            continue
        text = path.read_text()
        if not text.startswith("---\n"):
            continue
        parts = text.split("---\n", 2)
        if len(parts) < 3:
            logger.warning("Skipping %s: missing closing frontmatter delimiter", path)
            continue
        _, fm_str, _ = parts
        data = yaml.safe_load(fm_str) or {}
        try:
            persona = PersonaDefinition(**data)
        except (ValueError, TypeError) as exc:
            logger.warning("Skipping %s: %s", path, exc)
            continue
        if persona.status == PersonaStatus.stale:
            continue
        out.append(persona)
    return sorted(out, key=lambda p: (p.axis.value, p.slug))

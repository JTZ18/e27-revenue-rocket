"""Load persona definitions from kb/personas/."""
from pathlib import Path

import yaml

from intel_engine.schemas.persona import PersonaDefinition, PersonaStatus


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
        _, fm_str, _ = text.split("---\n", 2)
        data = yaml.safe_load(fm_str) or {}
        try:
            persona = PersonaDefinition(**data)
        except (ValueError, TypeError):
            continue
        if persona.status == PersonaStatus.stale:
            continue
        out.append(persona)
    return sorted(out, key=lambda p: (p.axis.value, p.slug))

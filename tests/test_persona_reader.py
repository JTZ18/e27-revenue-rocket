"""Test persona reader."""
from pathlib import Path

from intel_engine.personas.reader import load_personas
from intel_engine.schemas.persona import PersonaAxis


def _seed(kb_root: Path) -> None:
    (kb_root / "personas" / "interest").mkdir(parents=True)
    (kb_root / "personas" / "lifecycle").mkdir(parents=True)
    (kb_root / "personas" / "interest" / "health_conscious.md").write_text(
        "---\n"
        "axis: interest\n"
        "slug: health_conscious\n"
        "label: Health-conscious\n"
        "description: Cares about safety.\n"
        "signals: [BPA, vegan]\n"
        "status: active\n"
        "---\n\nBody.\n"
    )
    (kb_root / "personas" / "lifecycle" / "prospect.md").write_text(
        "---\n"
        "axis: lifecycle\n"
        "slug: prospect\n"
        "label: Prospect\n"
        "description: Pre-purchase.\n"
        "signals: [price match, comparison]\n"
        "status: active\n"
        "---\n\nBody.\n"
    )


def test_load_personas_returns_typed(tmp_path: Path):
    _seed(tmp_path / "kb")
    personas = load_personas(tmp_path / "kb")
    assert len(personas) == 2
    by_slug = {p.slug: p for p in personas}
    assert by_slug["health_conscious"].axis == PersonaAxis.interest
    assert by_slug["prospect"].axis == PersonaAxis.lifecycle


def test_load_personas_skips_stale(tmp_path: Path):
    _seed(tmp_path / "kb")
    (tmp_path / "kb" / "personas" / "interest" / "old.md").write_text(
        "---\n"
        "axis: interest\n"
        "slug: old\n"
        "label: Old\n"
        "description: deprecated\n"
        "signals: [x]\n"
        "status: stale\n"
        "---\n\nBody.\n"
    )
    personas = load_personas(tmp_path / "kb")
    assert all(p.slug != "old" for p in personas)

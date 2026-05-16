"""Test synthetic gap resolver."""
from datetime import date

from eval.synthetic_resolver import synthesise_resolution
from intel_engine.schemas.kb import KBDomain, KBStatus


def test_synthesise_creates_valid_kb_entry():
    entry = synthesise_resolution(
        ticket_id="TKT-9005",
        customer_question="Is the movement MRI safe?",
        question_type="knowledge_gap",
        themes_detected=["movement_safety"],
        today=date(2026, 5, 17),
    )

    assert entry.frontmatter.domain == KBDomain.faq
    assert entry.frontmatter.status == KBStatus.active
    assert entry.frontmatter.last_verified == date(2026, 5, 17)
    assert "replay" in entry.frontmatter.sources[0]
    assert entry.frontmatter.slug.startswith("synth-")
    assert "MRI safe" in entry.body


def test_synthesise_uses_question_type_as_theme_when_themes_empty():
    entry = synthesise_resolution(
        ticket_id="TKT-9999",
        customer_question="Some novel question",
        question_type="materials_safety",
        themes_detected=[],
        today=date(2026, 5, 17),
    )
    assert "materials_safety" in entry.frontmatter.themes


def test_synthesise_slug_is_stable_for_same_inputs():
    a = synthesise_resolution(
        ticket_id="TKT-9001",
        customer_question="Are your straps BPA-free?",
        question_type="materials_safety",
        themes_detected=["materials_safety"],
        today=date(2026, 5, 17),
    )
    b = synthesise_resolution(
        ticket_id="TKT-9001",
        customer_question="Are your straps BPA-free?",
        question_type="materials_safety",
        themes_detected=["materials_safety"],
        today=date(2026, 5, 17),
    )
    assert a.frontmatter.slug == b.frontmatter.slug

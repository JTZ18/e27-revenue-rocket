"""Test SOP seeding."""
from pathlib import Path

from intel_engine.schemas.kb import KBDomain, KBEntry
from scripts.seed_sop import write_escalation_policy, write_schema


def test_write_schema_is_plain_markdown(tmp_path: Path):
    body = "## Openers\n\nPreferred: 'Yes.'\nForbidden: 'Great question!'"
    out = tmp_path / "_schema.md"
    write_schema(body, out)
    assert out.read_text().startswith("# Brand Voice Contract")
    assert "Preferred: 'Yes.'" in out.read_text()


def test_write_escalation_policy_is_kb_entry(tmp_path: Path):
    body = "Escalate when: customer angry, warranty > damage, refund > 10 days"
    out = tmp_path / "policies" / "escalation.md"
    write_escalation_policy(body, out, source_file="05a_SOP.docx")

    entry = KBEntry.from_markdown(out.read_text())
    assert entry.frontmatter.domain == KBDomain.policy
    assert entry.frontmatter.slug == "escalation-policy"
    assert "warranty" in entry.body

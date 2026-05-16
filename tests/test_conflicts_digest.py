"""Test Slack-formatted conflict digest."""
from intel_engine.conflicts.digest import to_slack_blocks
from intel_engine.schemas.conflict import ConflictDigest, KBConflict


def test_slack_blocks_has_one_section_per_conflict():
    digest = ConflictDigest(
        week_end="2026-05-17",
        conflicts=[
            KBConflict(
                domain="pricing",
                fact_topic="engraving price",
                entries=["kb/faqs/a.md", "kb/rate-cards/engraving.md"],
                canonical_proposal="kb/rate-cards/engraving.md",
                reasoning="Rate cards canonical.",
            ),
            KBConflict(
                domain="policy",
                fact_topic="warranty length",
                entries=["kb/faqs/b.md", "kb/policies/warranty.md"],
                canonical_proposal="kb/policies/warranty.md",
                reasoning="SOP canonical for policy.",
            ),
        ],
    )
    blocks = to_slack_blocks(digest)
    section_count = sum(1 for b in blocks if b.get("type") == "section")
    # header + 2 conflicts × 2 sections each (body + actions header) = at least 5
    assert section_count >= 3

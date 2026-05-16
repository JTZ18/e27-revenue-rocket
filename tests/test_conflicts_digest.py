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
    # header + summary + 2 conflicts * (section + actions) = 6
    assert len(blocks) == 6
    action_blocks = [b for b in blocks if b.get("type") == "actions"]
    assert len(action_blocks) == 2
    action_ids = [
        elem["action_id"]
        for b in action_blocks
        for elem in b.get("elements", [])
        if "action_id" in elem
    ]
    assert len(action_ids) == len(set(action_ids)), "action_ids must be unique"


def test_slack_blocks_empty_digest():
    digest = ConflictDigest(
        week_end="2026-05-17",
        conflicts=[],
    )
    blocks = to_slack_blocks(digest)
    assert len(blocks) == 2  # header + summary only
    action_blocks = [b for b in blocks if b.get("type") == "actions"]
    assert len(action_blocks) == 0

"""Test conflict schemas."""
import pytest
from pydantic import ValidationError

from intel_engine.schemas.conflict import ConflictDigest, KBConflict


def test_kb_conflict_requires_two_entries():
    with pytest.raises(ValidationError):
        KBConflict(
            domain="pricing",
            fact_topic="engraving price",
            entries=["only-one"],
            canonical_proposal="only-one",
            reasoning="r",
        )


def test_conflict_digest_aggregates():
    digest = ConflictDigest(
        week_end="2026-05-17",
        conflicts=[
            KBConflict(
                domain="pricing",
                fact_topic="engraving price",
                entries=["faqs/engraving-old.md", "rate-cards/engraving.md"],
                canonical_proposal="rate-cards/engraving.md",
                reasoning="Rate card is canonical per kb/_schema.md.",
            )
        ],
    )
    assert digest.count == 1

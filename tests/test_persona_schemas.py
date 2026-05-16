"""Test persona schemas."""
import pytest
from pydantic import ValidationError

from intel_engine.schemas.persona import (
    PersonaAxis,
    PersonaDefinition,
    PersonaDriftReport,
    PersonaProposal,
)


def test_persona_axis_is_constrained():
    with pytest.raises(ValidationError):
        PersonaDefinition(
            axis="invalid_axis",
            slug="x",
            label="X",
            description="d",
            signals=["a"],
        )


def test_persona_definition_minimum_signals():
    p = PersonaDefinition(
        axis=PersonaAxis.interest,
        slug="health_conscious",
        label="Health-conscious",
        description="Cares about materials safety.",
        signals=["BPA", "vegan", "skin allergy"],
    )
    assert p.signals == ["BPA", "vegan", "skin allergy"]
    assert p.status == "active"


def test_persona_drift_report_carries_evidence():
    report = PersonaDriftReport(
        window_start="2026-04-01",
        window_end="2026-05-12",
        unmatched_tickets=4,
        threshold=3,
        proposals=[
            PersonaProposal(
                axis=PersonaAxis.interest,
                slug="sustainability_buyer",
                label="Sustainability buyer",
                description="Cares about carbon-neutral shipping and vegan materials.",
                signals=["carbon-neutral", "vegan", "sustainability"],
                example_ticket_ids=["TKT-1041", "TKT-1052", "TKT-1063"],
                rationale="Repeated mentions of sustainability not covered by health_conscious.",
            )
        ],
    )
    assert report.proposals[0].axis == PersonaAxis.interest
    assert report.unmatched_tickets >= report.threshold

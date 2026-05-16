"""Test theme schemas."""
import pytest
from pydantic import ValidationError

from intel_engine.schemas.theme import Theme, ThemeReport


def test_theme_requires_examples():
    with pytest.raises(ValidationError):
        Theme(slug="x", label="X", frequency=2, example_ticket_ids=[], summary="s")


def test_theme_report_aggregates():
    report = ThemeReport(
        week_start="2026-05-11",
        week_end="2026-05-17",
        ticket_count=42,
        themes=[
            Theme(
                slug="bpa_safety",
                label="BPA safety",
                frequency=5,
                example_ticket_ids=["T1", "T2"],
                summary="Recurring questions about BPA-free straps.",
            ),
            Theme(
                slug="sustainability",
                label="Sustainability",
                frequency=3,
                example_ticket_ids=["T3", "T4"],
                summary="Carbon-neutral + vegan strap questions.",
            ),
        ],
    )
    assert report.themes[0].frequency == 5
    assert report.top_slug() == "bpa_safety"

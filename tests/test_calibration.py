"""Test calibration agreement."""
from pathlib import Path

import pandas as pd

from eval.calibration import compute_agreement


def test_compute_agreement_perfect():
    human = pd.DataFrame(
        [
            {
                "ticket_id": "A",
                "grounded": 5, "brand_voice": 5, "completeness": 5,
                "no_hallucination": 5, "tone_fit": 5,
            },
            {
                "ticket_id": "B",
                "grounded": 3, "brand_voice": 3, "completeness": 3,
                "no_hallucination": 3, "tone_fit": 3,
            },
        ]
    )
    llm = human.copy()
    out = compute_agreement(human=human, llm=llm)
    assert out["mae"]["grounded"] == 0.0
    assert out["kappa"] == 1.0
    assert out["n"] == 2


def test_compute_agreement_imperfect():
    human = pd.DataFrame(
        [{"ticket_id": "A", "grounded": 5, "brand_voice": 5,
          "completeness": 5, "no_hallucination": 5, "tone_fit": 5}]
    )
    llm = pd.DataFrame(
        [{"ticket_id": "A", "grounded": 4, "brand_voice": 5,
          "completeness": 5, "no_hallucination": 5, "tone_fit": 5}]
    )
    out = compute_agreement(human=human, llm=llm)
    assert out["mae"]["grounded"] == 1.0

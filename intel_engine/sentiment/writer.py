"""Persist sentiment artefacts to external-intel/YYYY-MM/<theme>.json + git commit."""
import json
import os
import subprocess
from pathlib import Path

from intel_engine.schemas.sentiment import ExternalSentimentReport, SentimentComparison


def _month_from_ran_at(ran_at: str) -> str:
    # ran_at is ISO 8601 (e.g. 2026-05-17T10:00:00+08:00); take first 7 chars.
    return ran_at[:7]


def write_and_commit_sentiment(
    *,
    report: ExternalSentimentReport,
    comparison: SentimentComparison,
    repo_root: Path,
) -> str:
    """Write external-intel/YYYY-MM/<theme>.json then create one git commit."""
    if report.theme_slug != comparison.theme_slug:
        raise ValueError(
            f"theme_slug mismatch: report={report.theme_slug!r} "
            f"comparison={comparison.theme_slug!r}"
        )

    month = _month_from_ran_at(report.ran_at)
    out_dir = repo_root / "external-intel" / month
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{report.theme_slug}.json"

    payload = {
        "report": report.model_dump(mode="json"),
        "comparison": comparison.model_dump(mode="json"),
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True))

    env = os.environ.copy()
    subprocess.run(
        ["git", "add", str(out_path)],
        cwd=repo_root, env=env, check=True, capture_output=True,
    )
    subprocess.run(
        [
            "git", "-c", "commit.gpgsign=false", "commit",
            "-m", f"sentiment: {month}/{report.theme_slug} verdict={comparison.verdict.value}",
        ],
        cwd=repo_root, env=env, check=True, capture_output=True,
    )
    sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo_root, capture_output=True, text=True, check=True,
    ).stdout.strip()
    return sha

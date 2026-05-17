"""Persist monthly marketing brief to briefs/YYYY-MM-marketing-brief.md."""
import os
import subprocess
from pathlib import Path

from intel_engine.schemas.brief import MarketingBrief


def _render(brief: MarketingBrief) -> str:
    lines = [
        f"# Marketing Brief — {brief.month}",
        "",
        "## Headline",
        "",
        brief.headline,
        "",
        "## Insights",
        "",
    ]
    for insight in brief.insights:
        segments = ", ".join(insight.persona_segments) or "(all)"
        lines.extend(
            [
                f"### {insight.theme}  ({insight.ticket_count} tickets — {segments})",
                "",
                insight.observation,
                "",
            ]
        )
    lines.extend(["## Recommendations", ""])
    for rec in brief.recommendations:
        lines.extend(
            [
                f"- **[{rec.target.value}]** {rec.action}",
                f"  - Expected impact: {rec.expected_impact}",
                f"  - Evidence themes: {', '.join(rec.evidence_themes)}",
                "",
            ]
        )

    if brief.external_sentiment:
        lines.extend(["## External Sentiment (last30days)", ""])
        for cmp in brief.external_sentiment:
            lines.extend(
                [
                    f"### {cmp.theme_slug} — `{cmp.verdict.value}`",
                    "",
                    f"- Internal frequency: {cmp.internal_frequency}",
                    f"- External mentions (last 30 days): {cmp.external_mentions}",
                    "",
                    cmp.reasoning,
                    "",
                    f"**Suggested action:** {cmp.suggested_action}",
                    "",
                ]
            )
    return "\n".join(lines)


def write_and_commit_brief(brief: MarketingBrief, repo_root: Path) -> str:
    out_dir = repo_root / "briefs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{brief.month}-marketing-brief.md"
    out_path.write_text(_render(brief))

    env = os.environ.copy()
    subprocess.run(
        ["git", "add", str(out_path)],
        cwd=repo_root,
        env=env,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "git", "-c", "commit.gpgsign=false", "commit",
            "-m", f"briefs: monthly marketing brief {brief.month}",
        ],
        cwd=repo_root, env=env, check=True, capture_output=True,
    )
    sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo_root, capture_output=True, text=True, check=True,
    ).stdout.strip()
    return sha

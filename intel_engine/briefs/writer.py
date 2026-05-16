"""Persist monthly marketing brief to briefs/YYYY-MM-marketing-brief.md."""
import os
import subprocess
from pathlib import Path

from intel_engine.schemas.brief import MarketingBrief


def _render(brief: MarketingBrief) -> str:
    lines = [
        f"# Marketing Brief — {brief.month}",
        "",
        f"## Headline",
        "",
        brief.headline,
        "",
        "## Insights",
        "",
    ]
    for ins in brief.insights:
        segments = ", ".join(ins.persona_segments) or "(all)"
        lines.extend(
            [
                f"### {ins.theme}  ({ins.ticket_count} tickets — {segments})",
                "",
                ins.observation,
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
    return "\n".join(lines)


def write_and_commit_brief(brief: MarketingBrief, repo_root: Path) -> str:
    out_dir = repo_root / "briefs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{brief.month}-marketing-brief.md"
    out_path.write_text(_render(brief))

    env = os.environ.copy()
    subprocess.run(["git", "add", str(out_path)], cwd=repo_root, env=env, check=True)
    subprocess.run(
        [
            "git", "-c", "commit.gpgsign=false", "commit",
            "-m", f"briefs: monthly marketing brief {brief.month}",
        ],
        cwd=repo_root, env=env, check=True,
    )
    sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo_root, capture_output=True, text=True, check=True,
    ).stdout.strip()
    return sha

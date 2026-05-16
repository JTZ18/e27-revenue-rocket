"""Persist weekly theme reports to kb/themes/YYYY-MM-DD.md."""
import os
import subprocess
from pathlib import Path

from intel_engine.schemas.theme import ThemeReport


def _render(report: ThemeReport) -> str:
    lines = [
        f"# Weekly Theme Report — {report.week_end}",
        "",
        f"Window: {report.week_start} → {report.week_end}",
        f"Tickets analysed: {report.ticket_count}",
        "",
        "## Themes",
        "",
    ]
    for theme in sorted(report.themes, key=lambda t: t.frequency, reverse=True):
        lines.extend(
            [
                f"### {theme.label}",
                "",
                f"- slug: `{theme.slug}`",
                f"- frequency: {theme.frequency}",
                f"- examples: {', '.join(theme.example_ticket_ids)}",
                "",
                theme.summary,
                "",
            ]
        )
    return "\n".join(lines)


def write_and_commit_theme_report(report: ThemeReport, repo_root: Path) -> str:
    out_dir = repo_root / "kb" / "themes"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{report.week_end}.md"
    out_path.write_text(_render(report))

    env = os.environ.copy()
    subprocess.run(["git", "add", str(out_path)], cwd=repo_root, env=env, check=True)
    subprocess.run(
        [
            "git", "-c", "commit.gpgsign=false", "commit",
            "-m", f"themes: weekly report {report.week_end}",
        ],
        cwd=repo_root, env=env, check=True,
    )
    sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo_root, capture_output=True, text=True, check=True,
    ).stdout.strip()
    return sha

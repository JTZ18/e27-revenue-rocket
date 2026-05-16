"""Generate kb/index.md from all KB entries."""
from collections import defaultdict
from pathlib import Path

from intel_engine.kb.reader import load_kb


def generate_index(kb_root: Path, out_path: Path) -> None:
    entries = load_kb(kb_root)

    by_domain: dict[str, list] = defaultdict(list)
    for entry in entries:
        by_domain[entry.frontmatter.domain.value].append(entry)

    lines: list[str] = [
        "# Knowledge Base Index",
        "",
        "Generated automatically. Do not edit by hand — re-run "
        "`scripts/generate_index.py`.",
        "",
        f"Total active entries: {len(entries)}",
        "",
    ]
    for domain in sorted(by_domain.keys()):
        lines.append(f"## {domain}")
        lines.append("")
        for entry in sorted(by_domain[domain], key=lambda e: e.frontmatter.slug):
            fm = entry.frontmatter
            themes = ", ".join(fm.themes) if fm.themes else "—"
            lines.append(
                f"- **{fm.slug}** — {fm.title}  "
                f"_(themes: {themes})_"
            )
        lines.append("")

    out_path.write_text("\n".join(lines))


if __name__ == "__main__":
    generate_index(Path("kb"), Path("kb/index.md"))
    print("Wrote kb/index.md")

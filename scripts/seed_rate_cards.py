"""Convert rate card CSVs into KB markdown entries (domain=pricing)."""
import csv
from datetime import date
from pathlib import Path

from intel_engine.schemas.kb import KBDomain, KBEntry, KBFrontmatter


def _rows_to_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return ""
    headers = list(rows[0].keys())
    out = ["| " + " | ".join(h.replace("_", " ").title() for h in headers) + " |"]
    out.append("|" + "---|" * len(headers))
    for r in rows:
        cells = []
        for h in headers:
            val = r.get(h, "")
            if h == "price_sgd" and val:
                cells.append(f"SGD {val}")
            else:
                cells.append(val)
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def seed_rate_card(
    src: Path,
    out_path: Path,
    slug: str,
    title: str,
    themes: list[str],
) -> None:
    rows = list(csv.DictReader(src.open()))
    table = _rows_to_table(rows)

    entry = KBEntry(
        frontmatter=KBFrontmatter(
            slug=slug,
            title=title,
            domain=KBDomain.pricing,
            themes=themes,
            sources=[f"data/{src.name}"],
            last_verified=date.today(),
        ),
        body=table,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(entry.to_markdown())


if __name__ == "__main__":
    seed_rate_card(
        src=Path("data/03a_rate_card_engraving.csv"),
        out_path=Path("kb/rate-cards/engraving.md"),
        slug="engraving-rate-card",
        title="Engraving services — pricing, character limits, fonts, turnaround",
        themes=["engraving", "pricing"],
    )
    seed_rate_card(
        src=Path("data/03b_rate_card_servicing.csv"),
        out_path=Path("kb/rate-cards/servicing.md"),
        slug="servicing-rate-card",
        title="Watch servicing — tiers, pricing, turnaround",
        themes=["servicing", "pricing", "aftercare"],
    )
    print("Wrote kb/rate-cards/engraving.md and kb/rate-cards/servicing.md")

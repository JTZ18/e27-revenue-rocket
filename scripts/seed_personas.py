"""Seed 5 brief-derived personas as placeholder KB markdown.

These are seed entries; Plan 3 implements cold-start discovery and drift detection.
"""
from datetime import date
from pathlib import Path

from intel_engine.schemas.kb import KBDomain, KBEntry, KBFrontmatter

PERSONAS = [
    {
        "axis": "interest",
        "slug": "health-conscious-buyer",
        "title": "Health-Conscious Buyer",
        "body": (
            "Buyers prioritising BPA-free, nickel-free, hypoallergenic materials. "
            "Often buying for children or for skin-sensitive use cases. "
            "Trigger keywords: BPA-free, nickel allergy, hypoallergenic, kids, REACH, safe."
        ),
    },
    {
        "axis": "interest",
        "slug": "gifter",
        "title": "Gifter",
        "body": (
            "Buyers purchasing for someone else. Care about engraving, gift wrap, "
            "turnaround time, presentation. Trigger keywords: gift, engraving, "
            "birthday, anniversary, Father's Day, Valentine's, wrap."
        ),
    },
    {
        "axis": "interest",
        "slug": "enthusiast-collector",
        "title": "Enthusiast / Collector",
        "body": (
            "Watch enthusiasts who care about Grade 5 titanium, Miyota movement details, "
            "limited editions, craftsmanship. Trigger keywords: titanium grade, Miyota, "
            "limited edition, movement, craftsmanship."
        ),
    },
    {
        "axis": "interest",
        "slug": "active-outdoor-buyer",
        "title": "Active / Outdoor Buyer",
        "body": (
            "Buyers for trail running, diving, climbing. Care about water resistance, "
            "shock rating, FKM rubber strap. Trigger keywords: water resistance, shock, "
            "trail, dive, FKM, rubber strap, altitude."
        ),
    },
    {
        "axis": "interest",
        "slug": "sustainability-advocate",
        "title": "Sustainability Advocate",
        "body": (
            "Buyers focused on vegan straps, carbon-neutral shipping, eco packaging, "
            "take-back programmes. Trigger keywords: vegan, carbon offset, recycling, "
            "eco, sustainability."
        ),
    },
]


def main() -> None:
    out_root = Path("kb/personas/interest")
    out_root.mkdir(parents=True, exist_ok=True)
    for p in PERSONAS:
        entry = KBEntry(
            frontmatter=KBFrontmatter(
                slug=p["slug"],
                title=p["title"],
                domain=KBDomain.persona,
                themes=[p["axis"]],
                sources=["challenge_brief"],
                last_verified=date.today(),
            ),
            body=p["body"],
        )
        path = out_root / f"{p['slug']}.md"
        path.write_text(entry.to_markdown())
    print(f"Wrote {len(PERSONAS)} personas to kb/personas/interest/")


if __name__ == "__main__":
    main()

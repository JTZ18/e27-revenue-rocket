"""Deterministic synthetic resolution for the replay harness.

The harness can't ask a real human during replay. Instead it fabricates a
short KB entry grounded in the ticket text + the held-out question_type label,
so that subsequent tickets on the same topic can retrieve it.

This is intentionally simple — it is NOT the real kb_drafter agent. The point
of the replay is to show the *retrieval* curve improves as the KB grows, not
to show how good the drafter is (that is what the quality eval measures).
"""
import hashlib
import re
from datetime import date

from intel_engine.schemas.kb import KBDomain, KBEntry, KBFrontmatter, KBStatus

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(text: str, max_len: int = 40) -> str:
    cleaned = _SLUG_RE.sub("-", text.lower()).strip("-")
    return cleaned[:max_len].rstrip("-") or "entry"


def synthesise_resolution(
    *,
    ticket_id: str,
    customer_question: str,
    question_type: str,
    themes_detected: list[str],
    today: date,
) -> KBEntry:
    """Return a KBEntry the harness will write + commit on the agent's behalf."""
    base = _slugify(customer_question, max_len=30)
    digest = hashlib.sha1(
        f"{ticket_id}|{customer_question}".encode()
    ).hexdigest()[:6]
    slug = f"synth-{base}-{digest}"

    themes = themes_detected if themes_detected else [question_type]

    title = customer_question.rstrip("?.! ").strip()
    body = (
        f"Resolved via replay harness from ticket {ticket_id}.\n\n"
        f"Customer question: {customer_question}\n\n"
        f"Topic class: `{question_type}`. This entry was created automatically "
        f"during evaluation replay; in production it would be replaced by an "
        f"agent-drafted entry written from a CS team member's resolution."
    )

    return KBEntry(
        frontmatter=KBFrontmatter(
            slug=slug,
            title=title[:120] or f"Synthetic entry for {ticket_id}",
            domain=KBDomain.faq,
            themes=themes,
            sources=[f"replay:{ticket_id}"],
            last_verified=today,
            supersedes=[],
            status=KBStatus.active,
        ),
        body=body,
    )

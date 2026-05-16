"""Persist gap entries to disk."""
from pathlib import Path

from intel_engine.schemas.gap import Gap
from intel_engine.settings import gap_log_root


def write_gap(gap: Gap) -> Path:
    """Serialise gap to JSON-in-Markdown under GAP_LOG_ROOT."""
    root = gap_log_root()
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{gap.gap_id}.md"
    payload = gap.model_dump_json(indent=2)
    content = (
        f"# Gap: {gap.customer_question}\n\n"
        f"```json\n{payload}\n```\n"
    )
    path.write_text(content)
    return path


def load_gap(gap_id: str) -> Gap:
    """Read a gap by id."""
    path = gap_log_root() / f"{gap_id}.md"
    if not path.exists():
        raise FileNotFoundError(f"Gap not found: {gap_id}")
    text = path.read_text()
    # Extract the JSON block between ``` markers
    start = text.find("```json\n") + len("```json\n")
    end = text.find("\n```", start)
    payload = text[start:end]
    return Gap.model_validate_json(payload)


def update_gap(gap: Gap) -> Path:
    """Re-write an existing gap (e.g., after status change)."""
    return write_gap(gap)

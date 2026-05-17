"""Subprocess wrapper around the last30days.py CLI."""
import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path

from intel_engine.schemas.sentiment import ExternalSentimentReport, SentimentQueryPlan

logger = logging.getLogger(__name__)


class RunnerError(RuntimeError):
    """Raised when last30days.py fails or returns unparseable output."""


def _resolve_script() -> Path:
    raw = os.environ.get("LAST30DAYS_SCRIPT", "").strip()
    if not raw:
        raise RunnerError("LAST30DAYS_SCRIPT env var is not set")
    path = Path(raw).expanduser()
    if not path.exists():
        raise RunnerError(f"LAST30DAYS_SCRIPT not found at {path}")
    return path


def _resolve_python() -> str:
    return os.environ.get("LAST30DAYS_PYTHON", "python3").strip() or "python3"


def _count_mentions(emit: dict) -> int:
    total = 0
    for cluster in emit.get("clusters", []) or []:
        items = cluster.get("items") or []
        total += len(items)
    return total


def _top_sources(emit: dict, limit: int = 5) -> list[str]:
    seen: list[str] = []
    for cluster in emit.get("clusters", []) or []:
        src = cluster.get("source") or cluster.get("title")
        if src and src not in seen:
            seen.append(src)
        if len(seen) >= limit:
            break
    return seen


def _top_snippets(emit: dict, limit: int = 5) -> list[str]:
    out: list[str] = []
    for cluster in emit.get("clusters", []) or []:
        for item in (cluster.get("items") or [])[:2]:
            snippet = (item.get("snippet") or "").strip()
            if snippet:
                out.append(snippet[:240])
            if len(out) >= limit:
                return out
    return out


def run_last30days(
    *,
    theme_slug: str,
    plan: SentimentQueryPlan,
    ran_at: str,
    timeout_seconds: int = 240,
) -> ExternalSentimentReport:
    """Run last30days.py for one theme and return a typed report."""
    script = _resolve_script()
    python = _resolve_python()

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(plan.model_dump(mode="json"), fh)
        plan_path = fh.name

    cmd = [python, str(script), plan.topic, "--plan", plan_path, "--emit", "json"]
    logger.info("Invoking last30days: %s", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RunnerError(f"last30days timed out after {timeout_seconds}s") from exc
    finally:
        Path(plan_path).unlink(missing_ok=True)

    if result.returncode != 0:
        raise RunnerError(
            f"last30days exit {result.returncode}: {result.stderr.strip()[:500]}"
        )

    try:
        emit = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RunnerError(
            f"last30days returned non-JSON output: {result.stdout[:200]!r}"
        ) from exc

    return ExternalSentimentReport(
        theme_slug=theme_slug,
        ran_at=ran_at,
        topic=plan.topic,
        external_mentions=_count_mentions(emit),
        top_sources=_top_sources(emit),
        snippets=_top_snippets(emit),
        raw_emit=emit,
    )

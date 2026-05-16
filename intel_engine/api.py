"""FastAPI service exposing intel engine endpoints to n8n."""
import secrets
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()  # Load .env file

from intel_engine.agents.kb_drafter import draft_kb_entry
from intel_engine.agents.traversal import traverse
from intel_engine.gap.logger import load_gap, write_gap
from intel_engine.kb.writer import write_and_commit_entry
from intel_engine.schemas.event import CommonEvent
from intel_engine.schemas.gap import Gap, GapResolution, GapStatus
from intel_engine.schemas.kb import KBEntry
from intel_engine.schemas.traversal import TraversalResult

app = FastAPI(title="Boldr Intel Engine", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/traverse", response_model=TraversalResult)
async def traverse_endpoint(event: CommonEvent) -> TraversalResult:
    try:
        return await traverse(event)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Traversal failed: {e}") from e


class GapCreateRequest(BaseModel):
    source_event_id: str
    customer_question: str
    missing_info: list[str]
    themes_detected: list[str] = []
    persona_hints: list[str] = []


@app.post("/gap", response_model=Gap)
async def create_gap(payload: GapCreateRequest) -> Gap:
    today = datetime.now(UTC).date()
    gap_id = f"gap_{today.isoformat()}_{secrets.token_hex(3)}"
    gap = Gap(
        gap_id=gap_id,
        source_event_id=payload.source_event_id,
        customer_question=payload.customer_question,
        missing_info=payload.missing_info,
        themes_detected=payload.themes_detected,
        persona_hints=payload.persona_hints,
    )
    write_gap(gap)
    return gap


class GapResolveRequest(BaseModel):
    gap_id: str
    resolved_by: str
    resolution_text: str
    source_note: str | None = None


@app.post("/gap/resolve", response_model=Gap)
async def resolve_gap(payload: GapResolveRequest) -> Gap:
    gap = load_gap(payload.gap_id)
    gap.status = GapStatus.resolved
    gap.resolution = GapResolution(
        resolved_by=payload.resolved_by,
        resolution_text=payload.resolution_text,
        resolved_at=datetime.now(UTC),
        source_note=payload.source_note,
    )
    write_gap(gap)
    return gap


class DraftRequest(BaseModel):
    gap_id: str


@app.post("/draft-kb-entry", response_model=KBEntry)
async def draft_endpoint(payload: DraftRequest) -> KBEntry:
    gap = load_gap(payload.gap_id)
    if gap.resolution is None:
        raise HTTPException(status_code=400, detail="Gap is not resolved yet")
    try:
        return await draft_kb_entry(gap)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Draft failed: {e}") from e


class CommitRequest(BaseModel):
    entry: KBEntry
    approver: str
    gap_id: str | None = None


class CommitResponse(BaseModel):
    sha: str
    path: str


@app.post("/commit-to-kb", response_model=CommitResponse)
async def commit_endpoint(payload: CommitRequest) -> CommitResponse:
    from intel_engine.settings import kb_root
    repo_root = kb_root().parent
    try:
        sha = write_and_commit_entry(
            payload.entry,
            approver=payload.approver,
            repo_root=repo_root,
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Git commit failed: {e.stderr.decode() if e.stderr else e}",
        ) from e

    rel_path = (
        Path("kb") / payload.entry.frontmatter.domain.value
        / f"{payload.entry.frontmatter.slug}.md"
    )
    if payload.gap_id:
        gap = load_gap(payload.gap_id)
        gap.drafted_kb_slug = payload.entry.frontmatter.slug
        write_gap(gap)

    return CommitResponse(sha=sha, path=str(rel_path))


DRAFT_STAGE_DIR = Path("./kb-drafts-staging")


class StageDraftRequest(BaseModel):
    gap_id: str
    entry: KBEntry


@app.post("/draft/stage")
async def stage_draft(payload: StageDraftRequest) -> dict[str, str]:
    DRAFT_STAGE_DIR.mkdir(exist_ok=True)
    (DRAFT_STAGE_DIR / f"{payload.gap_id}.json").write_text(
        payload.entry.model_dump_json(indent=2)
    )
    return {"status": "staged"}


@app.get("/draft/staged/{gap_id}", response_model=KBEntry)
async def get_staged_draft(gap_id: str) -> KBEntry:
    path = DRAFT_STAGE_DIR / f"{gap_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No staged draft")
    return KBEntry.model_validate_json(path.read_text())

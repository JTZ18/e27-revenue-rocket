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

from intel_engine.agents.brief_writer import write_brief
from intel_engine.agents.conflict_detector import detect_conflicts
from intel_engine.agents.persona_discovery import discover_personas
from intel_engine.agents.persona_drift import detect_drift
from intel_engine.agents.theme_clusterer import cluster_themes
from intel_engine.conflicts.digest import to_slack_blocks
from intel_engine.personas.reader import load_personas
from intel_engine.schemas.theme import ThemeReport
from intel_engine.settings import kb_root

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


class UpdateDraftRequest(BaseModel):
    entry: KBEntry


@app.post("/draft/update")
async def update_draft(payload: UpdateDraftRequest, gap_id: str) -> dict[str, str]:
    path = DRAFT_STAGE_DIR / f"{gap_id}.json"
    path.write_text(payload.entry.model_dump_json(indent=2))
    return {"status": "updated"}


@app.post("/gap/approve", response_model=CommitResponse)
async def approve_draft(payload: CommitRequest) -> CommitResponse:
    """Approve a drafted KB entry — stage it then commit to Git."""
    # Stage first so we have a copy
    DRAFT_STAGE_DIR.mkdir(exist_ok=True)
    stage_path = DRAFT_STAGE_DIR / f"{payload.gap_id}.json"
    stage_path.write_text(payload.entry.model_dump_json(indent=2))

    # Commit to Git
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


@app.post("/gap/reject")
async def reject_draft(body: dict) -> dict[str, str]:
    """Discard a drafted KB entry — delete staged file, leave gap open."""
    gap_id = body.get("gap_id") or body.get("private_metadata", "")
    stage_path = DRAFT_STAGE_DIR / f"{gap_id}.json"
    if stage_path.exists():
        stage_path.unlink()
    return {"status": "rejected", "gap_id": gap_id}


class ViewSubmissionRequest(BaseModel):
    pass  # payload is raw JSON from Slack


@app.post("/slack/interactive-endpoint")
async def slack_interactive_endpoint(body: dict) -> dict:
    """Generic endpoint that routes view_submission callbacks."""
    view = body.get("view", {})
    callback_id = view.get("callback_id", "")
    private_metadata = view.get("private_metadata", "")
    user = body.get("user", {})
    view_state = view.get("state", {}).get("values", {})

    if callback_id == "gap_resolution":
        res_text = view_state.get("resolution_text", {}).get("resolution", {}).get("value", "")
        source_note = view_state.get("source_note", {}).get("note", {}).get("value", "")
        resolved_by = user.get("name", "")
        return {"status": "processed_gap_resolution", "gap_id": private_metadata}

    if callback_id == "edit_kb_entry":
        title = view_state.get("edit_title", {}).get("title", {}).get("value", "")
        slug = view_state.get("edit_slug", {}).get("slug", {}).get("value", "")
        domain_val = view_state.get("edit_domain", {}).get("domain", {}).get("value", "")
        body_text = view_state.get("edit_body", {}).get("body", {}).get("value", "")
        return {
            "status": "processed_edit",
            "gap_id": private_metadata,
            "title": title,
            "slug": slug,
            "domain": domain_val,
            "body": body_text
        }

    return {"status": "unknown_callback", "callback_id": callback_id}


class TicketsRequest(BaseModel):
    tickets: list[dict]


class WindowedTicketsRequest(BaseModel):
    tickets: list[dict]
    week_start: str
    week_end: str


class DriftRequest(BaseModel):
    tickets: list[dict]
    window_start: str
    window_end: str


class BriefRequest(BaseModel):
    month: str
    theme_reports: list[dict]
    kb_summary: str = ""


class ConflictsRequest(BaseModel):
    kb_entries: list[dict]
    week_end: str


@app.post("/personas/discover")
async def personas_discover(req: TicketsRequest) -> dict:
    try:
        proposals = await discover_personas(req.tickets)
        return {"proposals": [p.model_dump(mode="json") for p in proposals]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Persona discovery failed: {e}") from e


@app.post("/personas/drift")
async def personas_drift(req: DriftRequest) -> dict:
    try:
        active = load_personas(kb_root())
        report = await detect_drift(
            active_personas=active,
            tickets=req.tickets,
            window_start=req.window_start,
            window_end=req.window_end,
        )
        return report.model_dump(mode="json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Persona drift detection failed: {e}") from e


@app.post("/themes/cluster")
async def themes_cluster(req: WindowedTicketsRequest) -> dict:
    try:
        report = await cluster_themes(
            tickets=req.tickets,
            week_start=req.week_start,
            week_end=req.week_end,
        )
        return report.model_dump(mode="json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Theme clustering failed: {e}") from e


@app.post("/briefs/monthly")
async def briefs_monthly(req: BriefRequest) -> dict:
    try:
        personas = load_personas(kb_root())
        theme_reports = [ThemeReport(**r) for r in req.theme_reports]
        brief = await write_brief(
            month=req.month,
            theme_reports=theme_reports,
            personas=personas,
            kb_summary=req.kb_summary,
        )
        return brief.model_dump(mode="json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Brief generation failed: {e}") from e


@app.post("/conflicts/digest")
async def conflicts_digest(req: ConflictsRequest) -> dict:
    try:
        digest = await detect_conflicts(
            kb_entries=req.kb_entries,
            week_end=req.week_end,
        )
        return {
            **digest.model_dump(mode="json"),
            "count": digest.count,
            "slack_blocks": to_slack_blocks(digest),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conflict detection failed: {e}") from e

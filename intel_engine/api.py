"""FastAPI service exposing intel engine endpoints to n8n."""
from fastapi import FastAPI, HTTPException

from intel_engine.agents.traversal import traverse
from intel_engine.schemas.event import CommonEvent
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
        raise HTTPException(
            status_code=500, detail=f"Traversal failed: {e}"
        ) from e

"""FastAPI service exposing intel engine endpoints to n8n."""
from fastapi import FastAPI

app = FastAPI(title="Boldr Intel Engine", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

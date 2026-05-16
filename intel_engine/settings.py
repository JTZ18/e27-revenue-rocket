"""Environment-driven config."""
import os
from functools import cache
from pathlib import Path


@cache
def kb_root() -> Path:
    return Path(os.environ.get("KB_ROOT", "./kb")).resolve()


@cache
def gap_log_root() -> Path:
    return Path(os.environ.get("GAP_LOG_ROOT", "./gap-log")).resolve()


def llm_config(provider: str) -> dict[str, str]:
    """Return base_url, api_key, model for a provider ('minimax' or 'kimi')."""
    prefix = f"LLM_{provider.upper()}"
    return {
        "base_url": os.environ[f"{prefix}_BASE_URL"],
        "api_key": os.environ[f"{prefix}_API_KEY"],
        "model": os.environ[f"{prefix}_MODEL"],
    }

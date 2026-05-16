"""Shared pytest fixtures."""
import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _env_isolation(monkeypatch, tmp_path):
    """Each test starts with clean env and isolated paths."""
    monkeypatch.setenv("KB_ROOT", str(tmp_path / "kb"))
    monkeypatch.setenv("GAP_LOG_ROOT", str(tmp_path / "gap-log"))
    monkeypatch.setenv("LLM_MINIMAX_API_KEY", "test-key")
    monkeypatch.setenv("LLM_KIMI_API_KEY", "test-key")
    (tmp_path / "kb").mkdir()
    (tmp_path / "gap-log").mkdir()


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"

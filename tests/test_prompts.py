"""Test prompt loader."""
from pathlib import Path

import pytest

from intel_engine.llm.prompts import load_prompt


def test_load_prompt_reads_markdown_file(tmp_path: Path, monkeypatch):
    workflows_dir = tmp_path / "kb" / "_workflows"
    workflows_dir.mkdir(parents=True)
    (workflows_dir / "test-agent.md").write_text(
        "# Test Agent\n\nYou are a test assistant.\n"
    )
    monkeypatch.setenv("KB_ROOT", str(tmp_path / "kb"))

    text = load_prompt("test-agent")
    assert "You are a test assistant." in text


def test_load_prompt_raises_on_missing(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("KB_ROOT", str(tmp_path / "kb"))
    (tmp_path / "kb" / "_workflows").mkdir(parents=True)
    with pytest.raises(FileNotFoundError):
        load_prompt("does-not-exist")

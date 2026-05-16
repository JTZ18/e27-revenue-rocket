"""Test persona writer."""
import subprocess
from pathlib import Path

from intel_engine.personas.writer import write_and_commit_persona
from intel_engine.schemas.persona import PersonaAxis, PersonaDefinition


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "kb" / "personas" / "interest").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@x"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=repo, check=True)
    (repo / "README.md").write_text("seed")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "seed"],
        cwd=repo, check=True,
    )
    return repo


def test_writer_writes_under_axis_and_commits(tmp_path: Path):
    repo = _init_repo(tmp_path)
    persona = PersonaDefinition(
        axis=PersonaAxis.interest,
        slug="sustainability_buyer",
        label="Sustainability buyer",
        description="Cares about carbon-neutral shipping and vegan materials.",
        signals=["carbon-neutral", "vegan"],
    )

    sha = write_and_commit_persona(persona, approver="cs-alice", repo_root=repo)

    out_path = repo / "kb" / "personas" / "interest" / "sustainability_buyer.md"
    assert out_path.exists()
    assert "Sustainability buyer" in out_path.read_text()
    assert len(sha) >= 7

    log = subprocess.run(
        ["git", "log", "--oneline"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout
    assert "personas: add sustainability_buyer" in log

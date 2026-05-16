"""Write persona definitions + commit to git."""
import os
import subprocess
from pathlib import Path

import yaml

from intel_engine.schemas.persona import PersonaDefinition


def _render(persona: PersonaDefinition) -> str:
    fm = persona.model_dump(mode="json")
    body = persona.description
    return f"---\n{yaml.safe_dump(fm, sort_keys=False).strip()}\n---\n\n{body}\n"


def write_and_commit_persona(
    persona: PersonaDefinition,
    approver: str,
    repo_root: Path,
) -> str:
    """Write persona to kb/personas/<axis>/<slug>.md, commit, return short SHA."""
    out_dir = repo_root / "kb" / "personas" / persona.axis.value
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{persona.slug}.md"
    is_update = out_path.exists()
    out_path.write_text(_render(persona))

    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = os.environ.get("GIT_AUTHOR_NAME", "Intel Engine")
    env["GIT_AUTHOR_EMAIL"] = os.environ.get("GIT_AUTHOR_EMAIL", "intel-engine@local")
    env["GIT_COMMITTER_NAME"] = env["GIT_AUTHOR_NAME"]
    env["GIT_COMMITTER_EMAIL"] = env["GIT_AUTHOR_EMAIL"]

    msg = (
        f"personas: {'update' if is_update else 'add'} {persona.slug}\n\n"
        f"Axis: {persona.axis.value}\n"
        f"Label: {persona.label}\n"
        f"Signals: {', '.join(persona.signals)}\n\n"
        f"Approved by: {approver}\n"
    )
    subprocess.run(
        ["git", "add", str(out_path)],
        cwd=repo_root,
        env=env,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-m", msg],
        cwd=repo_root,
        env=env,
        check=True,
        capture_output=True,
    )
    sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return sha

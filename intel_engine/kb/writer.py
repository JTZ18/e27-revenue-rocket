"""Write KB entries and commit to git."""
import os
import subprocess
from pathlib import Path

from intel_engine.schemas.kb import KBEntry
from intel_engine.settings import kb_root


def _regenerate_index(kb_path: Path) -> None:
    from scripts.generate_index import generate_index

    generate_index(kb_path, kb_path / "index.md")


def write_and_commit_entry(
    entry: KBEntry,
    approver: str,
    repo_root: Path | None = None,
    commit_subject_prefix: str = "kb: add",
) -> str:
    """Write entry to kb/<domain>/<slug>.md, regen index, commit.

    Returns the short SHA of the new commit.
    """
    if repo_root is None:
        repo_root = kb_root().parent
    kb_dir = repo_root / "kb"

    domain_dir = kb_dir / entry.frontmatter.domain.value
    domain_dir.mkdir(parents=True, exist_ok=True)
    entry_path = domain_dir / f"{entry.frontmatter.slug}.md"

    is_update = entry_path.exists()
    entry_path.write_text(entry.to_markdown())

    _regenerate_index(kb_dir)

    subject_verb = "update" if is_update else "add"
    commit_msg = (
        f"kb: {subject_verb} {entry.frontmatter.slug}\n\n"
        f"Title: {entry.frontmatter.title}\n"
        f"Domain: {entry.frontmatter.domain.value}\n"
        f"Themes: {', '.join(entry.frontmatter.themes) or '(none)'}\n"
        f"Sources: {', '.join(entry.frontmatter.sources) or '(none)'}\n"
        f"\n"
        f"Approved by: {approver}\n"
    )

    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = os.environ.get("GIT_AUTHOR_NAME", "Intel Engine")
    env["GIT_AUTHOR_EMAIL"] = os.environ.get("GIT_AUTHOR_EMAIL", "intel-engine@local")
    env["GIT_COMMITTER_NAME"] = env["GIT_AUTHOR_NAME"]
    env["GIT_COMMITTER_EMAIL"] = env["GIT_AUTHOR_EMAIL"]

    subprocess.run(
        ["git", "add", str(entry_path.relative_to(repo_root)), "kb/index.md"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )

    # If the file was recreated with identical content (e.g. replay snapshot),
    # git add stages nothing. Skip the commit and return current HEAD.
    diff_index = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=repo_root,
        capture_output=True,
    )
    if diff_index.returncode == 0:
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return sha

    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-m", commit_msg],
        cwd=repo_root,
        check=True,
        capture_output=True,
        env=env,
    )
    sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return sha

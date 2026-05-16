"""Load versioned agent prompts from kb/_workflows/."""
from intel_engine.settings import kb_root


def load_prompt(name: str) -> str:
    """Read kb/_workflows/<name>.md, returning the prompt text."""
    path = kb_root() / "_workflows" / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text()

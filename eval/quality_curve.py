"""Render quality (rubric overall) over ticket index."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402


def render_quality_curve(
    *,
    scores_csv: Path,
    out_png: Path,
    title: str = "Draft quality over time (LLM-judge, rubric overall)",
    window: int = 5,
) -> float:
    df = pd.read_csv(scores_csv).sort_values("ticket_index").reset_index(drop=True)
    if df.empty:
        out_png.parent.mkdir(parents=True, exist_ok=True)
        out_png.touch()
        return 0.0

    rolling = df["overall"].rolling(window=window, min_periods=1).mean()

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.scatter(df["ticket_index"], df["overall"], s=14, alpha=0.55, label="Per draft")
    ax.plot(df["ticket_index"], rolling, linewidth=2, label=f"Rolling (w={window})")
    ax.set_xlabel("Ticket index")
    ax.set_ylabel("Rubric overall (1–5)")
    ax.set_ylim(1, 5)
    ax.set_title(title)
    ax.grid(True, alpha=0.25)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(out_png, dpi=144)
    plt.close(fig)
    return float(df["overall"].iloc[-1])

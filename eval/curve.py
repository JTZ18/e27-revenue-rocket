"""Render the headline answer-rate-over-time curve."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402


def render_curve(
    *,
    curve_data_csv: Path,
    out_png: Path,
    title: str = "Answer rate over time",
    window: int = 5,
) -> float:
    """Read curve_data.csv, draw rolling answer rate with SHA annotations.

    Returns the cumulative final answer rate.
    """
    df = pd.read_csv(curve_data_csv)
    df["answered"] = df["can_answer_fully"].astype(int)

    cumulative = df["answered"].cumsum() / (df.index + 1)
    rolling = df["answered"].rolling(window=window, min_periods=1).mean()

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.plot(df["ticket_index"], cumulative, label="Cumulative answer rate", linewidth=2)
    ax.plot(
        df["ticket_index"],
        rolling,
        label=f"Rolling (window={window})",
        linewidth=1.4,
        linestyle="--",
    )

    growth = df[df["kb_commit_sha"].notna() & (df["kb_commit_sha"].astype(str) != "")]
    for _, row in growth.iterrows():
        x = row["ticket_index"]
        y = cumulative.iloc[int(x)]
        ax.scatter([x], [y], marker="o", s=22, color="tab:orange", zorder=5)
        ax.annotate(
            str(row["kb_commit_sha"])[:7],
            xy=(x, y),
            xytext=(4, 6),
            textcoords="offset points",
            fontsize=7,
            color="tab:orange",
        )

    ax.set_xlabel("Ticket index (chronological)")
    ax.set_ylabel("Answer rate")
    ax.set_ylim(0, 1.05)
    ax.set_title(title)
    ax.grid(True, alpha=0.25)
    ax.legend(loc="lower right")

    fig.tight_layout()
    fig.savefig(out_png, dpi=144)
    plt.close(fig)

    return float(cumulative.iloc[-1]) if len(cumulative) else 0.0

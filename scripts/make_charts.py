#!/usr/bin/env python
"""Render the lead chart: nominal vs inflation-adjusted top films (dumbbell).

Uses the shared `lollipop` template (dumbbell mode) from shared/chart_templates.py.
Saves a twitter_landscape PNG with the @unwelcomedata watermark to outputs/social/.

Run: .venv/bin/python scripts/make_charts.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
WORKSPACE = PROJECT.parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(WORKSPACE / "shared"))

from src.ingest import load_config  # noqa: E402
from src.clean_quality import get_connection  # noqa: E402
from chart_templates import lollipop  # noqa: E402
from viz import PRESETS  # noqa: E402


def _millions_billions(v: float) -> str:
    """Format a dollar value compactly ($1.90B / $201M)."""
    if v >= 1_000_000_000:
        return f"${v / 1_000_000_000:.2f}B"
    return f"${v / 1_000_000:.0f}M"


def main(top_n: int = 15) -> None:
    cfg = load_config(str(PROJECT / "config.yaml"))
    con = get_connection(cfg)
    df = con.execute(
        f"""
        SELECT title, adjusted_gross, nominal_gross, release_year
        FROM films_adjusted
        ORDER BY adjusted_gross DESC
        LIMIT {top_n}
        """
    ).df()
    con.close()

    # Put the film's release year in the label for context ("Gone with the Wind (1939)").
    df["label"] = df["title"] + "  (" + df["release_year"].astype(str) + ")"

    img_w, img_h, _ = PRESETS["twitter_landscape"]
    img = lollipop(
        df,
        category_col="label",
        value_col="adjusted_gross",       # primary dot = adjusted (the honest board)
        value2_col="nominal_gross",       # second dot = what it actually made at the time
        value_fmt=_millions_billions,
        title="Hollywood's real box-office champions, once you adjust for inflation",
        subtitle="Top 15 domestic films by ticket-price-adjusted gross (2022 $) vs. their original nominal gross",
        source="Box Office Mojo, Top Lifetime Adjusted Grosses (domestic, adj. to 2022)",
        dot_color="#005F73",              # adjusted (teal, primary)
        dot2_color="#EE9B00",             # nominal (gold)
        value_label="Adjusted (2022 $)",
        value2_label="Nominal (release $)",
        img_width=img_w,
        img_height=img_h,
    )

    try:  # display inline when run in a notebook/IPython
        from IPython.display import display  # noqa
        display(img)
    except Exception:
        pass

    out_dir = Path(cfg["paths"]["outputs_social"])
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "01_adjusted_vs_nominal_top_films.png"
    img.save(out_path)
    print(f"Saved → {out_path}  ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    main()

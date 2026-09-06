#!/usr/bin/env python
"""Render the project's charts (all via the shared Pillow factory).

1. Domestic, inflation-adjusted top films (dumbbell: adjusted vs nominal).
2. Worldwide top films — domestic vs international split (dumbbell).
3. Genre over/under-index — which genres skew international vs domestic (diverging).

Each renders inline (when run in a notebook) and saves to outputs/social/.
Run: .venv/bin/python scripts/make_charts.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
WORKSPACE = PROJECT.parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(WORKSPACE / "shared"))

import duckdb  # noqa: E402

from src.ingest import load_config  # noqa: E402
from chart_templates import lollipop, single_ranked_bars, stacked_100pct_bars  # noqa: E402
from viz import PRESETS  # noqa: E402


def money_bil(v: float) -> str:
    return f"${v / 1e9:.2f}B" if abs(v) >= 1e9 else f"${v / 1e6:.0f}M"


def _display(img):
    try:
        from IPython.display import display
        display(img)
    except Exception:
        pass


def main() -> None:
    cfg = load_config(str(PROJECT / "config.yaml"))
    db_file = cfg["settings"]["duckdb_file"]
    # This script only reads. Try read-only; if a notebook kernel holds a
    # read-write lock (DuckDB is single-writer), fall back to a throwaway copy so
    # chart rendering never contends with an open notebook.
    try:
        con = duckdb.connect(db_file, read_only=True)
    except duckdb.IOException:
        import shutil, tempfile
        tmp = Path(tempfile.gettempdir()) / "hgf_charts_readcopy.duckdb"
        shutil.copy(db_file, tmp)
        print(f"(primary DB locked — reading from copy {tmp})")
        con = duckdb.connect(str(tmp), read_only=True)
    img_w, img_h, _ = PRESETS["twitter_landscape"]
    out = Path(cfg["paths"]["outputs_social"])
    out.mkdir(parents=True, exist_ok=True)

    # ── 1. Domestic adjusted vs nominal (relabeled clearly as DOMESTIC) ──────
    dom = con.execute(
        "SELECT title, adjusted_gross, nominal_gross, release_year "
        "FROM films_adjusted ORDER BY adjusted_gross DESC LIMIT 15"
    ).df()
    dom["label"] = dom["title"] + "  (" + dom["release_year"].astype(str) + ")"
    img1 = lollipop(
        dom, category_col="label", value_col="adjusted_gross", value2_col="nominal_gross",
        value_fmt=money_bil,
        title="The all-time top 15 domestic films, adjusted for inflation",
        subtitle="Ranked by inflation-adjusted U.S. & Canada gross. Teal = adjusted to 2022 $, gold = what each film actually made at the time (nominal).",
        source="Box Office Mojo, Top Lifetime Adjusted Grosses (domestic, adj. to 2022) — as of Sep 2026",
        dot_color="#005F73", dot2_color="#EE9B00",
        value_label="Adjusted (2022 $)", value2_label="Nominal (release $)",
        img_width=img_w, img_height=img_h,
    )
    _display(img1)
    img1.save(out / "01_domestic_adjusted_vs_nominal.png")

    # ── 2. Worldwide top films — home (US/Canada) vs abroad ──────────────────
    # Restrict to US-produced films so "domestic" (US & Canada box office) means
    # the film's HOME market. Non-US films (e.g. Chinese blockbusters) are excluded
    # here — for them US/Canada isn't home — and analysed separately.
    # 100% stacked bar of the split (home % vs abroad %), ordered by share abroad
    # so the teal segment shrinks down the list — the visual matches the sort.
    # (A dumbbell of absolute dollars can't do this: line length = dollar gap, which
    # doesn't track the percentage order.)
    ww = con.execute(
        """
        WITH us AS (SELECT title, release_year FROM films_genre WHERE is_us = TRUE),
        top AS (
            SELECT w.title, w.release_year,
                   100.0*w.foreign_gross/w.worldwide_gross AS foreign_pct,
                   100.0*w.domestic_gross/w.worldwide_gross AS home_pct
            FROM films_worldwide w JOIN us ON us.title=w.title AND us.release_year=w.release_year
            ORDER BY w.worldwide_gross DESC LIMIT 15
        )
        SELECT * FROM top ORDER BY foreign_pct DESC
        """
    ).df()
    ww["label"] = ww["title"] + "  (" + ww["release_year"].astype(str) + ")"
    img2 = stacked_100pct_bars(
        ww, group_col="label",
        segments=[
            {"col": "home_pct", "label": "Home (US/Canada)", "color": "#EE9B00"},
            {"col": "foreign_pct", "label": "Rest of world", "color": "#005F73"},
        ],
        title="Hollywood films: share of box office earned at home vs abroad",
        subtitle="Top 15 U.S.-produced films by worldwide gross, ordered by share earned abroad.",
        source="Box Office Mojo, Top Lifetime Grosses (Worldwide) + TMDB origin country — as of Sep 2026",
        bar_height=34, bar_gap=12, img_width=img_w, img_height=img_h,
    )
    _display(img2)
    img2.save(out / "02_worldwide_domestic_vs_international.png")

    # ── 3. Share of box office earned abroad, by genre (US films) ────────────
    # Plain international share per genre — no index, no zero-line. Each film's
    # gross is attributed to all its genres (ratio, so double-counting is fine).
    genre = con.execute(
        """
        WITH us AS (SELECT title, release_year FROM films_genre WHERE is_us = TRUE)
        SELECT gl.genre AS category, COUNT(*) n,
               ROUND(100.0*SUM(w.foreign_gross)/(SUM(w.domestic_gross)+SUM(w.foreign_gross)),1) AS value
        FROM films_worldwide w
        JOIN us ON us.title=w.title AND us.release_year=w.release_year
        JOIN film_genres_long gl ON gl.title=w.title AND gl.release_year=w.release_year
        GROUP BY gl.genre HAVING COUNT(*) >= 10
        ORDER BY value DESC
        """
    ).df()
    genre["pct_label"] = genre["value"].apply(lambda v: f"{v:.0f}%")
    img3 = single_ranked_bars(
        genre, category_col="category", value_col="value", total_label_col="pct_label",
        bar_color="#005F73",
        title="Every blockbuster genre earns most of its money abroad",
        subtitle="Share of worldwide box office earned OUTSIDE the U.S. & Canada, by genre (top U.S.-made films). Even the lowest — sci-fi — takes ~61% overseas.",
        source="Box Office Mojo (Worldwide) + TMDB genres/origin — as of Sep 2026",
        img_width=img_w, img_height=img_h,
    )
    _display(img3)
    img3.save(out / "03_genre_share_earned_abroad.png")

    con.close()
    print("Saved 3 charts to", out)


if __name__ == "__main__":
    main()

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

from src.ingest import load_config  # noqa: E402
from src.clean_quality import get_connection  # noqa: E402
from chart_templates import lollipop, diverging_bars  # noqa: E402
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
    con = get_connection(cfg)
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
        title="The biggest DOMESTIC films of all time, adjusted for inflation",
        subtitle="U.S. & Canada box office only. Teal = adjusted to 2022 $, gold = nominal (release $). Domestic figures — see the worldwide view for the fuller picture.",
        source="Box Office Mojo, Top Lifetime Adjusted Grosses (domestic, adj. to 2022) — as of Sep 2026",
        dot_color="#005F73", dot2_color="#EE9B00",
        value_label="Adjusted (2022 $)", value2_label="Nominal (release $)",
        img_width=img_w, img_height=img_h,
    )
    _display(img1)
    img1.save(out / "01_domestic_adjusted_vs_nominal.png")

    # ── 2. Worldwide top films — domestic vs international split ──────────────
    ww = con.execute(
        "SELECT title, release_year, domestic_gross, foreign_gross, worldwide_gross "
        "FROM films_worldwide ORDER BY worldwide_gross DESC LIMIT 15"
    ).df()
    ww["label"] = ww["title"] + "  (" + ww["release_year"].astype(str) + ")"
    img2 = lollipop(
        ww, category_col="label", value_col="foreign_gross", value2_col="domestic_gross",
        value_fmt=money_bil,
        title="Where the money really comes from: overseas",
        subtitle="Top 15 films by worldwide gross (nominal $). Teal = international (rest of world), gold = domestic (U.S. & Canada).",
        source="Box Office Mojo, Top Lifetime Grosses (Worldwide) — as of Sep 2026",
        dot_color="#005F73", dot2_color="#EE9B00",
        value_label="International", value2_label="Domestic (US/Canada)",
        img_width=img_w, img_height=img_h,
    )
    _display(img2)
    img2.save(out / "02_worldwide_domestic_vs_international.png")

    # ── 3. Genre over/under-index (international vs domestic lean) ────────────
    genre = con.execute(
        """
        WITH fg AS (
            SELECT w.domestic_gross, w.foreign_gross, g.genre
            FROM films_worldwide w
            JOIN film_genres_long g ON g.title=w.title AND g.release_year=w.release_year
        ),
        tot AS (SELECT SUM(domestic_gross) d, SUM(foreign_gross) f FROM fg),
        bygenre AS (
            SELECT genre, COUNT(*) n, SUM(domestic_gross) dom, SUM(foreign_gross) intl
            FROM fg GROUP BY genre HAVING COUNT(*) >= 10
        )
        SELECT genre AS category,
               ROUND((intl/(SELECT f FROM tot)) / NULLIF(dom/(SELECT d FROM tot),0) - 1, 3) AS value
        FROM bygenre
        ORDER BY value DESC
        """
    ).df()
    # value > 0 => over-indexes international; < 0 => skews domestic
    genre["label"] = genre["value"].apply(lambda v: f"{'+' if v >= 0 else ''}{v*100:.0f}%")
    img3 = diverging_bars(
        genre, category_col="category", value_col="value", label_col="label",
        title="Which genres travel? Blockbuster genres that skew overseas vs. at home",
        subtitle="Share of international box office relative to domestic, top-200 worldwide films (genres with 10+ films). Right = over-indexes internationally; left = skews domestic.",
        source="Box Office Mojo (Worldwide) + TMDB genres — as of Sep 2026",
        pos_color="#005F73", neg_color="#AE2012",
        img_width=img_w, img_height=img_h,
    )
    _display(img3)
    img3.save(out / "03_genre_international_vs_domestic_index.png")

    con.close()
    print("Saved 3 charts to", out)


if __name__ == "__main__":
    main()

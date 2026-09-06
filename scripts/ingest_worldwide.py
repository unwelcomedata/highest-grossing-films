#!/usr/bin/env python
"""Ingest + clean the Box Office Mojo WORLDWIDE lifetime-gross chart.

Adds the domestic-vs-international dimension the adjusted-domestic chart lacks:
per film, the worldwide / domestic / foreign lifetime gross (nominal $) and the
domestic/foreign split. Lands the `films_worldwide` table in DuckDB.

Run: .venv/bin/python scripts/ingest_worldwide.py
"""

from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from src.ingest import load_config, fetch_html  # noqa: E402
from src.clean_quality import (  # noqa: E402
    get_connection, load_to_duckdb, run_sql, register_source, save_interim,
)

RAW_HTML = "bom_ww_top_lifetime.html"


def main() -> None:
    cfg = load_config(str(PROJECT / "config.yaml"))
    url = cfg["sources"]["bom_worldwide"]["url"]
    raw_path = Path(cfg["paths"]["data_raw"]) / RAW_HTML
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    if raw_path.exists():
        print(f"Using cached raw HTML: {raw_path}")
        html = raw_path.read_text(encoding="utf-8")
    else:
        print(f"Fetching {url}")
        html = fetch_html(url)
        raw_path.write_text(html, encoding="utf-8")
        print(f"Saved raw HTML -> {raw_path}")

    raw = pd.read_html(StringIO(html))[0]
    print(f"Parsed {len(raw)} rows, columns: {list(raw.columns)}")

    con = get_connection(cfg)
    load_to_duckdb(raw, "bom_ww_raw", con)

    films = run_sql(
        """
        WITH cleaned AS (
            SELECT
                CAST("Rank" AS INTEGER) AS rank_worldwide,
                "Title" AS title,
                CAST("Year" AS INTEGER) AS release_year,
                -- money -> BIGINT; a bare '-' (no market gross) becomes NULL
                TRY_CAST(NULLIF(REGEXP_REPLACE("Worldwide Lifetime Gross", '[$,]', '', 'g'), '-') AS BIGINT) AS worldwide_gross,
                TRY_CAST(NULLIF(REGEXP_REPLACE("Domestic Lifetime Gross",  '[$,]', '', 'g'), '-') AS BIGINT) AS domestic_gross,
                TRY_CAST(NULLIF(REGEXP_REPLACE("Foreign Lifetime Gross",   '[$,]', '', 'g'), '-') AS BIGINT) AS foreign_gross
            FROM bom_ww_raw
        )
        SELECT
            rank_worldwide, title, worldwide_gross, domestic_gross, foreign_gross, release_year,
            ROUND(100.0 * domestic_gross / NULLIF(worldwide_gross, 0), 1) AS domestic_pct,
            ROUND(100.0 * foreign_gross  / NULLIF(worldwide_gross, 0), 1) AS foreign_pct
        FROM cleaned
        ORDER BY worldwide_gross DESC
        """,
        con,
    )
    load_to_duckdb(films, "films_worldwide", con)
    save_interim(films, cfg, "films_worldwide.parquet")

    register_source(
        con, "films_worldwide",
        name="Box Office Mojo - Top Lifetime Grosses (Worldwide)",
        url=url,
        license="Data (c) IMDb/Box Office Mojo; used for commentary/analysis.",
        notes=("Worldwide/domestic/foreign lifetime gross (NOMINAL, year-of-release dollars) "
               "with domestic%/foreign% split. Domestic = US & Canada. Not inflation-adjusted."),
        methodology="Studio-reported theatrical receipts; lifetime totals include re-releases.",
        series_breaks="Nominal dollars, not comparable across eras; worldwide totals favor recent, wide-release films.",
    )

    print(f"\nfilms_worldwide: {len(films)} rows")
    print(films.head(10).to_string(index=False))
    print("\nMost international (lowest domestic %):")
    print(films.nsmallest(5, "domestic_pct")[["title", "release_year", "worldwide_gross", "domestic_pct"]].to_string(index=False))
    con.close()


if __name__ == "__main__":
    main()

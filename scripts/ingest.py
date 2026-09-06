#!/usr/bin/env python
"""Ingest + clean the Box Office Mojo adjusted-gross chart into DuckDB.

Pipeline (raw → DuckDB → analysis table):
  1. Fetch the BOM "Top Lifetime Adjusted Grosses" page (adjust_gross_to=2022)
     and save the raw HTML to data/raw/ (untouched).
  2. Parse the single table into a DataFrame.
  3. Clean in DuckDB: strip $/commas, cast to numeric, derive decade + the
     inflation multiple (adjusted / nominal).
  4. Register provenance in _sources and save interim Parquet.

Run: .venv/bin/python scripts/ingest.py
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

RAW_HTML = "bom_top_lifetime_adjusted_2022.html"


def main() -> None:
    cfg = load_config(str(PROJECT / "config.yaml"))
    src = cfg["sources"]["bom_adjusted"]
    url = src["url"]
    adjust_year = src.get("adjust_to_year", 2022)
    raw_path = Path(cfg["paths"]["data_raw"]) / RAW_HTML
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Fetch (or reuse cached raw HTML) — raw lands untouched.
    if raw_path.exists():
        print(f"Using cached raw HTML: {raw_path}")
        html = raw_path.read_text(encoding="utf-8")
    else:
        print(f"Fetching {url}")
        html = fetch_html(url)
        raw_path.write_text(html, encoding="utf-8")
        print(f"Saved raw HTML → {raw_path}")

    # 2. Parse the single chart table.
    raw = pd.read_html(StringIO(html))[0]
    print(f"Parsed {len(raw)} rows, columns: {list(raw.columns)}")

    con = get_connection(cfg)
    load_to_duckdb(raw, "bom_raw", con)

    # 3. Clean in DuckDB: money strings → BIGINT, derive decade + multiple.
    films = run_sql(
        """
        SELECT
            CAST("Rank" AS INTEGER)                                   AS rank_adjusted,
            "Title"                                                   AS title,
            CAST(REGEXP_REPLACE("Adj. Lifetime Gross", '[$,]', '', 'g') AS BIGINT) AS adjusted_gross,
            CAST(REGEXP_REPLACE("Lifetime Gross",       '[$,]', '', 'g') AS BIGINT) AS nominal_gross,
            CAST("Est. Num Tickets" AS BIGINT)                        AS est_tickets,
            CAST("Year" AS INTEGER)                                   AS release_year,
            (CAST("Year" AS INTEGER) // 10) * 10                      AS decade,
            ROUND(
                CAST(REGEXP_REPLACE("Adj. Lifetime Gross", '[$,]', '', 'g') AS DOUBLE)
                / NULLIF(CAST(REGEXP_REPLACE("Lifetime Gross", '[$,]', '', 'g') AS DOUBLE), 0),
                2
            )                                                         AS inflation_multiple
        FROM bom_raw
        ORDER BY adjusted_gross DESC
        """,
        con,
    )
    load_to_duckdb(films, "films_adjusted", con)
    save_interim(films, cfg, "films_adjusted.parquet")

    # 4. Provenance.
    register_source(
        con,
        "films_adjusted",
        name="Box Office Mojo — Top Lifetime Adjusted Grosses (domestic)",
        url=url,
        license="Data © IMDb/Box Office Mojo; used for commentary/analysis.",
        notes=(
            f"Domestic (US/Canada) lifetime grosses. Adjusted gross expressed in "
            f"{adjust_year} dollars via estimated tickets sold × {adjust_year} average "
            f"ticket price (ticket-price inflation, NOT CPI). Columns: rank_adjusted, "
            f"title, adjusted_gross, nominal_gross, est_tickets, release_year, decade, "
            f"inflation_multiple (adjusted/nominal)."
        ),
        methodology=(
            "Box Office Mojo estimates tickets sold and multiplies by a reference-year "
            "average ticket price. Re-releases are included in a film's lifetime total."
        ),
        series_breaks=(
            "Nominal grosses are in year-of-release dollars and are NOT comparable across "
            "eras without the adjustment. Older films' totals include decades of re-releases."
        ),
    )

    print(f"\nfilms_adjusted: {len(films)} rows")
    print(films.head(10).to_string(index=False))
    con.close()


if __name__ == "__main__":
    main()

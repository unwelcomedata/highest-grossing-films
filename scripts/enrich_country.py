#!/usr/bin/env python
"""Enrich films with country of origin from TMDB, and flag US-produced films.

The box-office "domestic" field means U.S. & Canada — which only equals a film's
HOME market for US-produced films. To keep the domestic-vs-international analysis
consistent (home vs abroad), we fetch each film's origin country from TMDB and add
`origin_country` / `is_us` to films_genre. Analyses then restrict to US films.

Requires TMDB_API_KEY in .env. Run: .venv/bin/python scripts/enrich_country.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from src.ingest import load_config, load_env, tmdb_movie_country  # noqa: E402
from src.clean_quality import get_connection, load_to_duckdb, register_source, save_interim  # noqa: E402


def main() -> None:
    cfg = load_config(str(PROJECT / "config.yaml"))
    load_env(str(PROJECT / ".env"))
    api_key = os.environ.get("TMDB_API_KEY")
    if not api_key:
        raise SystemExit("TMDB_API_KEY missing from .env")

    con = get_connection(cfg)
    films = con.execute(
        "SELECT title, release_year, tmdb_id FROM films_genre WHERE tmdb_id IS NOT NULL"
    ).df()
    print(f"Fetching origin country for {len(films)} films (cached in data/raw/tmdb/)...")

    rows = []
    for i, r in films.iterrows():
        c = tmdb_movie_country(int(r["tmdb_id"]), api_key, cfg)
        rows.append({
            "tmdb_id": int(r["tmdb_id"]),
            "origin_country": ", ".join(c["origin_country"]) if c["origin_country"] else None,
            "is_us": c["is_us"],
        })
        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{len(films)}")

    country = pd.DataFrame(rows)

    # Merge onto films_genre (rebuild the table with the two new columns).
    fg = con.execute("SELECT * FROM films_genre").df()
    fg = fg.merge(country, on="tmdb_id", how="left")
    load_to_duckdb(fg, "films_genre", con)
    save_interim(fg, cfg, "films_genre.parquet")

    register_source(
        con, "films_genre",
        name="TMDB - film genres + country of origin",
        url="https://www.themoviedb.org/",
        license="TMDB API; non-commercial attribution.",
        notes=("Genre(s) + origin country per film (TMDB), matched by title+year. "
               "is_us flags films with the U.S. among origin/production countries — "
               "used to keep domestic-vs-international analyses to films for which "
               "'domestic' (US & Canada box office) is the home market."),
        methodology="TMDB /search/movie then /movie/{id} for origin_country/production_countries.",
        series_breaks="",
    )

    us = int(fg["is_us"].sum())
    print(f"\nfilms_genre: {len(fg)} films, {us} US-produced, {len(fg)-us} non-US")
    print("\nNon-US films in the worldwide top 200 (the 'broke into other markets' set):")
    non_us = con.execute("""
        SELECT w.rank_worldwide, w.title, g.origin_country,
               ROUND(w.worldwide_gross/1e9,2) ww_b, w.domestic_pct
        FROM films_worldwide w JOIN films_genre g
          ON g.title=w.title AND g.release_year=w.release_year
        WHERE g.is_us = FALSE
        ORDER BY w.worldwide_gross DESC LIMIT 20
    """).df()
    print(non_us.to_string(index=False))
    con.close()


if __name__ == "__main__":
    main()

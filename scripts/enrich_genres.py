#!/usr/bin/env python
"""Enrich the film lists with genre from TMDB.

Looks up every film across the worldwide + adjusted-domestic boards (deduped by
title+year), stores genres, and lands a `films_genre` table + a
`film_genres_long` table (one row per film x genre) for market analysis.

Requires a TMDB v3 key in .env: TMDB_API_KEY.

Run: .venv/bin/python scripts/enrich_genres.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from src.ingest import load_config, load_env, tmdb_lookup_movie  # noqa: E402
from src.clean_quality import (  # noqa: E402
    get_connection, load_to_duckdb, register_source, save_interim,
)


def main() -> None:
    cfg = load_config(str(PROJECT / "config.yaml"))
    load_env(str(PROJECT / ".env"))
    api_key = os.environ.get("TMDB_API_KEY")
    if not api_key:
        raise SystemExit("TMDB_API_KEY not found in .env")

    con = get_connection(cfg)

    # Union of films from both boards (title + year), deduped.
    films = con.execute(
        """
        SELECT DISTINCT title, release_year FROM (
            SELECT title, release_year FROM films_worldwide
            UNION
            SELECT title, release_year FROM films_adjusted
        )
        ORDER BY title
        """
    ).df()
    print(f"Looking up {len(films)} unique films on TMDB (cached in data/raw/tmdb/)...")

    records = []
    for i, row in films.iterrows():
        rec = tmdb_lookup_movie(row["title"], int(row["release_year"]), api_key, cfg)
        records.append(rec)
        if (i + 1) % 25 == 0:
            print(f"  {i + 1}/{len(films)}")

    genre_df = pd.DataFrame(records)
    genre_df["genres_str"] = genre_df["genres"].apply(lambda g: ", ".join(g) if g else None)

    unmatched = genre_df[~genre_df["matched"]]
    if len(unmatched):
        print(f"\n⚠ {len(unmatched)} unmatched (no TMDB result):")
        print(unmatched[["title", "year"]].to_string(index=False))

    # films_genre: one row per film with primary + all genres (drop list col for DuckDB)
    films_genre = genre_df.drop(columns=["genres"]).rename(columns={"year": "release_year"})
    load_to_duckdb(films_genre, "films_genre", con)
    save_interim(films_genre, cfg, "films_genre.parquet")

    # film_genres_long: one row per (title, release_year, genre) for aggregation
    long_rows = []
    for rec in records:
        for g in rec["genres"]:
            long_rows.append({"title": rec["title"], "release_year": rec["year"], "genre": g})
    long_df = pd.DataFrame(long_rows)
    load_to_duckdb(long_df, "film_genres_long", con)
    save_interim(long_df, cfg, "film_genres_long.parquet")

    register_source(
        con, "films_genre",
        name="TMDB (The Movie Database) - film genres",
        url="https://www.themoviedb.org/",
        license="TMDB API; genre metadata used under TMDB terms (non-commercial attribution).",
        notes=("Genre(s) per film, matched by title + release year via TMDB search. "
               "primary_genre = TMDB's first-listed genre. Some films may be unmatched "
               "(foreign titles, disambiguation) and carry null genre."),
        methodology="TMDB /search/movie by title+year; first result taken. Genres are TMDB's editorial tags.",
        series_breaks="",
    )

    matched = int(genre_df["matched"].sum())
    print(f"\nfilms_genre: {len(films_genre)} rows ({matched} matched, {len(films_genre)-matched} unmatched)")
    print(f"film_genres_long: {len(long_df)} rows")
    print("\nTop primary genres:")
    print(films_genre["primary_genre"].value_counts().head(10).to_string())
    con.close()


if __name__ == "__main__":
    main()

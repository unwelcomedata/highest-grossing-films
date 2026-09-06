# Scripts

Fun-tier project — no public one-command reproducible pipeline is required. The
walkthrough lives in the numbered `notebooks/` (01-ingest → 06-viz-social). These
scripts are the same logic in linear form, handy for a full rebuild.

## Run order

```bash
python scripts/ingest.py            # BOM adjusted-domestic chart  -> DuckDB (films_adjusted)
python scripts/ingest_worldwide.py  # BOM worldwide chart          -> DuckDB (films_worldwide)
python scripts/enrich_genres.py     # TMDB genre lookup per film    -> DuckDB (films_genre, film_genres_long)
python scripts/make_charts.py       # render the 3 charts           -> outputs/social/
```

- `ingest.py` / `ingest_worldwide.py` fetch each Box Office Mojo chart (or reuse
  the cached raw HTML in `data/raw/`), clean in DuckDB, register provenance in
  `_sources`, and save interim Parquet.
- `enrich_genres.py` needs a TMDB v3 key in `.env` (`TMDB_API_KEY`, gitignored).
  It looks up each film by title + year and caches responses in `data/raw/tmdb/`,
  so re-runs are offline.
- `make_charts.py` builds all three charts via the shared Pillow factory.
- The exports (CSV + codebook for each of the three tables) are produced by
  `notebooks/03-prepare.ipynb`.

## Notes

- The chart is rendered by the shared Pillow factory (`shared/chart_templates.py`
  → `lollipop`), not matplotlib. matplotlib is not used in this project (and does
  not run in its Python 3.14 venv due to a `MarkerStyle` deepcopy recursion).
- `scripts/_build_notebooks.py` is a one-off dev helper that generated the
  numbered notebooks; it is not part of the pipeline.

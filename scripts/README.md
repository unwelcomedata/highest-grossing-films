# Scripts

Fun-tier project — no public one-command reproducible pipeline is required. The
walkthrough lives in the numbered `notebooks/` (01-ingest → 06-viz-social). These
scripts are the same logic in linear form, handy for a full rebuild.

## Run order

```bash
python scripts/ingest.py            # BOM adjusted-domestic chart  -> DuckDB (films_adjusted)
python scripts/ingest_worldwide.py  # BOM worldwide chart          -> DuckDB (films_worldwide)
python scripts/enrich_genres.py     # TMDB genre + origin lookup    -> DuckDB (films_genre, films_foreign_us)
python scripts/make_charts.py       # render the 3 charts           -> outputs/social/
python scripts/validate_charts.py   # PRE-PUBLISH GATE (see below)   -> exits non-zero on any failure
```

## ⭐ Pre-publish validation gate — `validate_charts.py`

**Run this and confirm it exits 0 before curating the release branch or flipping
the repo public.** It re-derives what each of the three published charts should
show directly from the DuckDB source, and fails (non-zero exit) if:

- an export CSV in `export/` has drifted from its DuckDB source table,
- a headline chart fact changed (top film per chart + a spot-check dollar value),
- a structural invariant breaks (worldwide = domestic + foreign; CPI-adjusted >=
  nominal; expected row counts; the displayed foreign-language top 15 are
  predominantly non-U.S. origin).

```bash
.venv/bin/python scripts/validate_charts.py   # RESULT: all N checks passed - safe to publish.
```

If it reports a drift, regenerate the exports (`notebooks/03-prepare.ipynb`) and
re-render charts (`06-viz-social.ipynb`) until it passes. Do not publish on a
failure.

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

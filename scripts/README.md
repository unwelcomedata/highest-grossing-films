# Scripts

Fun-tier project — no public one-command reproducible pipeline is required. The
walkthrough lives in the numbered `notebooks/` (01-ingest → 06-viz-social). These
scripts are the same logic in linear form, handy for a full rebuild.

## Run order

```bash
python scripts/ingest.py        # fetch Box Office Mojo adjusted chart -> data/raw/ -> DuckDB (films_adjusted)
python scripts/make_charts.py   # render the lollipop/dumbbell lead chart -> outputs/social/
```

`scripts/ingest.py` fetches the source (or reuses the cached raw HTML in
`data/raw/`), cleans it in DuckDB, registers provenance in `_sources`, and saves
interim Parquet. The export (CSV + codebook) is produced by `notebooks/03-prepare.ipynb`.

## Notes

- The chart is rendered by the shared Pillow factory (`shared/chart_templates.py`
  → `lollipop`), not matplotlib. matplotlib is not used in this project (and does
  not run in its Python 3.14 venv due to a `MarkerStyle` deepcopy recursion).
- `scripts/_build_notebooks.py` is a one-off dev helper that generated the
  numbered notebooks; it is not part of the pipeline.

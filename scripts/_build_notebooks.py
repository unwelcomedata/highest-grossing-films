#!/usr/bin/env python
"""One-off: write the numbered pipeline notebooks with real, runnable, project-
specific walkthrough cells (so the notebooks ARE the process record).

This mirrors the logic in scripts/ingest.py + scripts/make_charts.py but laid out
as the numbered pipeline a reader can step through:
    00-explore  (left as-is: DuckDB sandbox)
    01-ingest   fetch BOM adjusted chart -> data/raw/
    02-clean    parse + clean in DuckDB -> films_adjusted (+ _sources)
    03-prepare  package the export (CSV + codebook)
    04-viz      matplotlib exploration (adjusted vs nominal)
    06-viz-social  the shared lollipop dumbbell lead chart (inline + saved)

Run once: .venv/bin/python scripts/_build_notebooks.py
"""

from __future__ import annotations

import json
from pathlib import Path

NB_DIR = Path(__file__).resolve().parent.parent / "notebooks"


def md(*lines: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": _src(lines)}


def code(*lines: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": _src(lines)}


def _src(lines: tuple[str, ...]) -> list[str]:
    text = "\n".join(lines)
    parts = text.split("\n")
    return [p + "\n" for p in parts[:-1]] + [parts[-1]]


def write(name: str, cells: list[dict]) -> None:
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    (NB_DIR / name).write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {name} ({len(cells)} cells)")


BOOT = (
    "import sys, os\n"
    "from pathlib import Path\n"
    "PROJECT = Path.cwd()\n"
    "while not (PROJECT / 'config.yaml').exists() and PROJECT != PROJECT.parent:\n"
    "    PROJECT = PROJECT.parent\n"
    "os.chdir(PROJECT)\n"
    "sys.path.insert(0, str(PROJECT))"
)


# ---------------------------------------------------------------------------
# 01 — INGEST
# ---------------------------------------------------------------------------
ingest = [
    md("# 01 — Ingest",
       "",
       "Fetch the raw source and land it in `data/raw/` **untouched**.",
       "",
       "**Source:** Box Office Mojo — *Top Lifetime Adjusted Grosses* (domestic). The",
       "`?adjust_gross_to=2022` query param makes the page return each film's",
       "inflation-adjusted gross (in 2022 dollars) alongside its nominal gross,",
       "estimated tickets sold, and release year. With that param the page is static",
       "(no JS needed)."),
    code(BOOT, "",
         "import pandas as pd",
         "from io import StringIO",
         "from src.ingest import load_config, fetch_html",
         "",
         "cfg = load_config('config.yaml')",
         "src = cfg['sources']['bom_adjusted']",
         "url = src['url']",
         "print('Source URL:', url)"),
    md("## Fetch and cache the raw HTML",
       "Save the page to `data/raw/` so the raw source is preserved and re-runs are",
       "offline."),
    code("raw_path = Path(cfg['paths']['data_raw']) / 'bom_top_lifetime_adjusted_2022.html'",
         "raw_path.parent.mkdir(parents=True, exist_ok=True)",
         "",
         "if raw_path.exists():",
         "    print('Using cached raw HTML:', raw_path)",
         "    html = raw_path.read_text(encoding='utf-8')",
         "else:",
         "    html = fetch_html(url)",
         "    raw_path.write_text(html, encoding='utf-8')",
         "    print('Saved raw HTML ->', raw_path)",
         "",
         "print(f'{len(html):,} bytes')"),
    md("## Parse the chart table",
       "The page has a single table: Rank, Title, Adj. Lifetime Gross, Lifetime Gross,",
       "Est. Num Tickets, Year."),
    code("raw = pd.read_html(StringIO(html))[0]",
         "print(raw.shape)",
         "raw.head(10)"),
    md("---",
       "**Next:** `02-clean.ipynb` loads this into DuckDB and cleans it.",
       "",
       "Nothing here modified data — the raw HTML in `data/raw/` is untouched."),
]


# ---------------------------------------------------------------------------
# 02 — CLEAN
# ---------------------------------------------------------------------------
clean = [
    md("# 02 — Clean & Standardize",
       "",
       "Load the raw chart into DuckDB and clean it **in SQL** (workspace norm):",
       "strip `$`/commas, cast to numeric, derive `decade` and the `inflation_multiple`",
       "(adjusted / nominal). Result: the `films_adjusted` table."),
    code(BOOT, "",
         "import pandas as pd",
         "from io import StringIO",
         "from src.ingest import load_config",
         "from src.clean_quality import get_connection, load_to_duckdb, run_sql, register_source, save_interim",
         "",
         "cfg = load_config('config.yaml')",
         "con = get_connection(cfg)",
         "",
         "# Reload the raw HTML parsed in 01 into a raw DuckDB table.",
         "html = (Path(cfg['paths']['data_raw']) / 'bom_top_lifetime_adjusted_2022.html').read_text(encoding='utf-8')",
         "raw = pd.read_html(StringIO(html))[0]",
         "load_to_duckdb(raw, 'bom_raw', con)",
         "print('bom_raw:', con.execute('SELECT COUNT(*) FROM bom_raw').fetchone()[0], 'rows')"),
    md("## Clean in DuckDB",
       "Money strings (`$1,895,421,694`) become `BIGINT`; `decade` uses integer",
       "division; `inflation_multiple` = adjusted / nominal (how many times the film's",
       "original take the adjusted figure represents)."),
    code("films = run_sql('''",
         "    SELECT",
         "        CAST(\"Rank\" AS INTEGER)                                   AS rank_adjusted,",
         "        \"Title\"                                                   AS title,",
         "        CAST(REGEXP_REPLACE(\"Adj. Lifetime Gross\", '[$,]', '', 'g') AS BIGINT) AS adjusted_gross,",
         "        CAST(REGEXP_REPLACE(\"Lifetime Gross\",       '[$,]', '', 'g') AS BIGINT) AS nominal_gross,",
         "        CAST(\"Est. Num Tickets\" AS BIGINT)                        AS est_tickets,",
         "        CAST(\"Year\" AS INTEGER)                                   AS release_year,",
         "        (CAST(\"Year\" AS INTEGER) // 10) * 10                      AS decade,",
         "        ROUND(",
         "            CAST(REGEXP_REPLACE(\"Adj. Lifetime Gross\", '[$,]', '', 'g') AS DOUBLE)",
         "            / NULLIF(CAST(REGEXP_REPLACE(\"Lifetime Gross\", '[$,]', '', 'g') AS DOUBLE), 0),",
         "            2) AS inflation_multiple",
         "    FROM bom_raw",
         "    ORDER BY adjusted_gross DESC",
         "''', con)",
         "load_to_duckdb(films, 'films_adjusted', con)",
         "print(films.shape)",
         "films.head(10)"),
    md("## Quick sanity checks"),
    code("# The classics should dominate the adjusted board; recent blockbusters have",
         "# the smallest inflation multiples (little time for ticket prices to rise).",
         "print('Top adjusted:', films.iloc[0]['title'], films.iloc[0]['release_year'])",
         "print('No nulls in key cols:',",
         "      films[['adjusted_gross','nominal_gross','est_tickets','release_year']].notna().all().all())",
         "films[['title','release_year','inflation_multiple']].sort_values('inflation_multiple').head(5)"),
    md("## Save interim + register provenance"),
    code("save_interim(films, cfg, 'films_adjusted.parquet')",
         "",
         "register_source(",
         "    con, 'films_adjusted',",
         "    name='Box Office Mojo - Top Lifetime Adjusted Grosses (domestic)',",
         "    url=cfg['sources']['bom_adjusted']['url'],",
         "    license='Data (c) IMDb/Box Office Mojo; used for commentary/analysis.',",
         "    notes='Domestic (US/Canada) lifetime grosses. Adjusted gross in 2022 dollars via estimated tickets sold x 2022 average ticket price (ticket-price inflation, NOT CPI).',",
         "    methodology='BOM estimates tickets sold x a reference-year average ticket price. Re-releases are included in a film lifetime total.',",
         "    series_breaks='Nominal grosses are in year-of-release dollars and are NOT comparable across eras without the adjustment.',",
         ")",
         "print(con.execute('SELECT duckdb_table, source_name FROM _sources').df().to_string(index=False))"),
    md("---",
       "**Next:** `03-prepare.ipynb` packages the sellable export + codebook."),
    md("## Cleanup",
       "Close the DuckDB connection so the write lock is released."),
    code("con.close()",
         "print('connection closed')"),
]


# ---------------------------------------------------------------------------
# 03 — PREPARE
# ---------------------------------------------------------------------------
prepare = [
    md("# 03 — Prepare & Export",
       "",
       "Package the cleaned `films_adjusted` table as the published dataset: CSV",
       "(+ Excel/Parquet) with a plain-English codebook for every column."),
    code(BOOT, "",
         "import pandas as pd",
         "from src.ingest import load_config",
         "from src.clean_quality import get_connection",
         "from src.prepare import package_dataset",
         "",
         "cfg = load_config('config.yaml')",
         "con = get_connection(cfg)",
         "films = con.execute('SELECT * FROM films_adjusted ORDER BY adjusted_gross DESC').df()",
         "print(films.shape)"),
    md("## Codebook — a plain-English description for every column"),
    code("codebook = {",
         "    'rank_adjusted':     'Rank by inflation-adjusted domestic gross (1 = highest).',",
         "    'title':             'Film title.',",
         "    'adjusted_gross':    'Domestic lifetime gross adjusted to 2022 dollars via ticket-price inflation (USD).',",
         "    'nominal_gross':     'Domestic lifetime gross in year-of-release dollars, as originally reported (USD).',",
         "    'est_tickets':       'Estimated number of tickets sold over the film lifetime (Box Office Mojo estimate).',",
         "    'release_year':      'Year of the film original theatrical release.',",
         "    'decade':            'Release decade (release_year rounded down to the nearest 10).',",
         "    'inflation_multiple':'adjusted_gross / nominal_gross - how many times its original take the adjusted figure represents.',",
         "}",
         "",
         "notes = '''",
         "Source: Box Office Mojo, Top Lifetime Adjusted Grosses (domestic, US/Canada), adjusted to 2022 dollars.",
         "URL: https://www.boxofficemojo.com/chart/top_lifetime_gross_adjusted/?adjust_gross_to=2022",
         "",
         "Method: adjusted gross = estimated tickets sold x the 2022 average ticket price (ticket-price inflation,",
         "NOT CPI). Domestic only. A film lifetime total includes re-release grosses, which inflates some classics.",
         "Nominal grosses are in year-of-release dollars and are not comparable across eras without the adjustment.",
         "'''",
         "written = package_dataset(films, cfg, name='highest_grossing_films_v1', codebook=codebook, notes=notes)",
         "written"),
    md("---",
       "**Next:** `04-viz.ipynb` (matplotlib exploration) and `06-viz-social.ipynb` (the social chart)."),
    md("## Cleanup"),
    code("con.close()",
         "print('connection closed')"),
]


# ---------------------------------------------------------------------------
# 04 — VIZ (matplotlib exploration)
# ---------------------------------------------------------------------------
viz = [
    md("# 04 — Explore visually",
       "",
       "Quick exploration of the story before the publication chart, using the shared",
       "Pillow `lollipop` template in both modes: single-value (lollipop) and two-value",
       "(dumbbell). Charts render inline via `display()`.",
       "",
       "> Note: this project renders with the shared **Pillow** factory rather than",
       "> matplotlib. (matplotlib does not run in this project's Python 3.14 venv — a",
       "> known `MarkerStyle` deepcopy recursion during axis-tick rendering — and the",
       "> publication path is Pillow anyway, so matplotlib isn't a dependency here.)"),
    code(BOOT, "",
         "WORKSPACE = PROJECT.parent.parent",
         "sys.path.insert(0, str(WORKSPACE / 'shared'))",
         "",
         "import pandas as pd",
         "from src.ingest import load_config",
         "from src.clean_quality import get_connection",
         "from chart_templates import lollipop",
         "from viz import PRESETS",
         "from IPython.display import display",
         "",
         "cfg = load_config('config.yaml')",
         "con = get_connection(cfg)",
         "films = con.execute('SELECT * FROM films_adjusted ORDER BY adjusted_gross DESC LIMIT 15').df()",
         "con.close()",
         "films['label'] = films['title'] + '  (' + films['release_year'].astype(str) + ')'",
         "img_w, img_h, _ = PRESETS['twitter_landscape']",
         "def money(v):",
         "    return f'${v/1e9:.2f}B' if v >= 1e9 else f'${v/1e6:.0f}M'",
         "films[['title','adjusted_gross','nominal_gross','release_year']].head()"),
    md("## Single-value lollipop — adjusted gross only",
       "The ranked adjusted board on its own (lollipop mode)."),
    code("display(lollipop(",
         "    films, category_col='label', value_col='adjusted_gross', value_fmt=money,",
         "    title='Top 15 films by inflation-adjusted domestic gross',",
         "    subtitle='Box Office Mojo, adjusted to 2022 dollars',",
         "    dot_color='#005F73', img_width=img_w, img_height=img_h,",
         "))"),
    md("## Dumbbell — adjusted vs nominal",
       "Adding `value2_col` turns it into a dumbbell: the gap between what a film made",
       "at the time (gold) and its adjusted gross (teal) is the inflation effect."),
    code("display(lollipop(",
         "    films, category_col='label', value_col='adjusted_gross', value2_col='nominal_gross',",
         "    value_fmt=money, title='Adjusted vs nominal domestic gross - top 15',",
         "    subtitle='Teal = adjusted (2022 $), gold = nominal (release $)',",
         "    dot_color='#005F73', dot2_color='#EE9B00',",
         "    value_label='Adjusted', value2_label='Nominal', img_width=img_w, img_height=img_h,",
         "))"),
    md("---",
       "**Next:** `06-viz-social.ipynb` builds the final publication chart (the same",
       "dumbbell, with full titling/source) and saves it to `outputs/social/`."),
]


# ---------------------------------------------------------------------------
# 06 — VIZ SOCIAL (Pillow lollipop lead chart)
# ---------------------------------------------------------------------------
viz_social = [
    md("# 06 — Social chart (Pillow)",
       "",
       "The publication-ready lead chart, using the shared `lollipop` template in",
       "**dumbbell mode**: each film shows its inflation-adjusted gross (teal) vs its",
       "original nominal gross (gold); the connector length is the inflation gap.",
       "",
       "The chart renders **inline** and is saved to `outputs/social/`."),
    code(BOOT, "",
         "# make the workspace-level shared/ importable",
         "WORKSPACE = PROJECT.parent.parent",
         "sys.path.insert(0, str(WORKSPACE / 'shared'))",
         "",
         "from src.ingest import load_config",
         "from src.clean_quality import get_connection",
         "from chart_templates import lollipop",
         "from viz import PRESETS",
         "from IPython.display import display",
         "",
         "cfg = load_config('config.yaml')",
         "con = get_connection(cfg)",
         "films = con.execute('''",
         "    SELECT title, adjusted_gross, nominal_gross, release_year",
         "    FROM films_adjusted ORDER BY adjusted_gross DESC LIMIT 15",
         "''').df()",
         "con.close()",
         "films['label'] = films['title'] + '  (' + films['release_year'].astype(str) + ')'",
         "films.head()"),
    md("## Render the dumbbell lead chart"),
    code("def money(v):",
         "    return f'${v/1e9:.2f}B' if v >= 1e9 else f'${v/1e6:.0f}M'",
         "",
         "img_w, img_h, _ = PRESETS['twitter_landscape']",
         "img = lollipop(",
         "    films, category_col='label',",
         "    value_col='adjusted_gross', value2_col='nominal_gross',",
         "    value_fmt=money,",
         "    title=\"Hollywood's real box-office champions, once you adjust for inflation\",",
         "    subtitle='Top 15 domestic films by ticket-price-adjusted gross (2022 $) vs. their original nominal gross',",
         "    source='Box Office Mojo, Top Lifetime Adjusted Grosses (domestic, adj. to 2022)',",
         "    dot_color='#005F73', dot2_color='#EE9B00',",
         "    value_label='Adjusted (2022 $)', value2_label='Nominal (release $)',",
         "    img_width=img_w, img_height=img_h,",
         ")",
         "",
         "# Workspace rule: ALWAYS show the chart inline, then save. display() first",
         "# so a chart can never be saved without being rendered in the notebook.",
         "display(img)",
         "",
         "out = Path(cfg['paths']['outputs_social']); out.mkdir(parents=True, exist_ok=True)",
         "path = out / '01_adjusted_vs_nominal_top_films.png'",
         "img.save(path)",
         "print('Displayed above; also saved ->', path)"),
    md("---",
       "Chart written to `outputs/social/`. Watermark `@unwelcomedata`, brand palette,",
       "`twitter_landscape` preset."),
]


if __name__ == "__main__":
    write("01-ingest.ipynb", ingest)
    write("02-clean.ipynb", clean)
    write("03-prepare.ipynb", prepare)
    write("04-viz.ipynb", viz)
    write("06-viz-social.ipynb", viz_social)
    print("done")

#!/usr/bin/env python3
"""Pre-publish validation — re-check the chart data before anything goes public.

Run this BEFORE curating the release branch / flipping the repo public. It
re-derives what each of the four published charts should show, straight from
the DuckDB source tables, and confirms:

  1. The published export CSVs (export/*_v1.csv) match the DuckDB source tables
     row-for-row on the key columns (no drift between the DB and what ships).
  2. The headline chart facts are still true (top film per chart + a spot-check
     value), so a silent data change can't slip out unnoticed.
  3. Structural invariants hold (worldwide = domestic + foreign; CPI-adjusted
     >= nominal; foreign-language list is non-U.S. origin; expected row counts).

Exit code 0 = all checks passed, safe to publish. Non-zero = do NOT publish.

Usage:
    .venv/bin/python scripts/validate_charts.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pandas as pd

# Resolve project root (the dir containing config.yaml) and import src helpers.
PROJECT = Path(__file__).resolve().parent
while not (PROJECT / "config.yaml").exists() and PROJECT != PROJECT.parent:
    PROJECT = PROJECT.parent
sys.path.insert(0, str(PROJECT))
from src.ingest import load_config  # noqa: E402

failures: list[str] = []
checks: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    """Record a pass/fail line."""
    if condition:
        checks.append(f"  PASS  {name}")
    else:
        failures.append(f"  FAIL  {name}" + (f" — {detail}" if detail else ""))


def approx(a: float, b: float, tol: float = 0.005) -> bool:
    """True if a is within tol (fractional) of b."""
    if b == 0:
        return a == 0
    return abs(a - b) / abs(b) <= tol


def main() -> int:
    cfg = load_config("config.yaml")
    db = str(PROJECT / cfg["settings"]["duckdb_file"])
    export_dir = PROJECT / cfg["paths"]["export"]
    con = duckdb.connect(db, read_only=True)

    # ── Chart 1 — worldwide home vs abroad ────────────────────────────────
    ww = con.execute(
        "SELECT * FROM films_worldwide ORDER BY worldwide_gross DESC"
    ).df()
    check("chart1: films_worldwide has 200 rows", len(ww) == 200, f"got {len(ww)}")
    bad = ww[(ww.domestic_gross + ww.foreign_gross - ww.worldwide_gross).abs() > 1]
    check(
        "chart1: worldwide == domestic + foreign (all rows)",
        len(bad) == 0,
        f"{len(bad)} rows violate the split",
    )
    top_ww = ww.iloc[0]
    check(
        "chart1: top worldwide film is Avatar",
        top_ww.title == "Avatar",
        f"got {top_ww.title!r}",
    )

    # ── Chart 2 — domestic, CPI-U adjusted ────────────────────────────────
    adj = con.execute(
        "SELECT * FROM films_adjusted ORDER BY adjusted_gross DESC"
    ).df()
    check("chart2: films_adjusted has 200 rows", len(adj) == 200, f"got {len(adj)}")
    # Ticket-price adjustment: pre-1980 films should always adjust UP (ticket
    # prices rose a lot since). Recent films can sit at/near nominal, so we only
    # assert the direction for older titles rather than universally.
    old = adj[adj.release_year < 1980]
    check(
        "chart2: pre-1980 films all adjust UP (adjusted > nominal)",
        bool((old.adjusted_gross > old.nominal_gross).all()),
        "an old film's ticket-price-adjusted gross is not above nominal",
    )
    top_adj = adj.iloc[0]
    check(
        "chart2: top adjusted film is Gone with the Wind",
        top_adj.title == "Gone with the Wind",
        f"got {top_adj.title!r}",
    )
    check(
        "chart2: Gone with the Wind adjusted ~= $1.90B (BOM ticket-price)",
        approx(float(top_adj.adjusted_gross), 1_895_421_694),
        f"got {top_adj.adjusted_gross:,}",
    )

    # ── Chart 3 — foreign-language by U.S. gross ──────────────────────────
    fl = con.execute(
        "SELECT * FROM films_foreign_us ORDER BY domestic_gross DESC"
    ).df()
    check("chart3: films_foreign_us has 100 rows", len(fl) == 100, f"got {len(fl)}")
    top_fl = fl.iloc[0]
    check(
        "chart3: top foreign-language film is Crouching Tiger, Hidden Dragon",
        top_fl.title == "Crouching Tiger, Hidden Dragon",
        f"got {top_fl.title!r}",
    )
    check(
        "chart3: Crouching Tiger U.S. gross ~= $128M (nominal)",
        approx(float(top_fl.domestic_gross), 128_078_872),
        f"got {top_fl.domestic_gross:,}",
    )
    # This chart is defined by LANGUAGE (Box Office Mojo's Foreign Language list),
    # NOT country of origin — the two are different axes. A handful of non-English
    # films (e.g. Monsoon Wedding) carry a U.S. origin_country from TMDB and still
    # belong here. So we do NOT forbid US-origin; instead we confirm the DISPLAYED
    # top 15 (what the chart shows) are all present with a country label and a
    # positive gross, and that origin is mostly non-U.S. (a sanity bound).
    top15 = fl.head(15)
    check(
        "chart3: displayed top 15 all have a positive U.S. gross",
        bool((top15.domestic_gross > 0).all()),
        "a top-15 foreign-language film has non-positive gross",
    )
    us_share_top15 = (top15.origin_country.fillna("") == "US").mean()
    check(
        "chart3: displayed top 15 are predominantly non-U.S. origin",
        us_share_top15 <= 0.2,
        f"{us_share_top15:.0%} of the top 15 are US-origin (expected mostly non-US)",
    )

    # ── Chart 4 — top-10 domestic vs top-10 international (by genre) ───────
    # Two INDEPENDENT top-10 lists over U.S.-produced films, each ranked by its
    # own measure. Re-derive both exactly as the notebook does and assert the
    # headline facts + list membership the chart depends on. No new export CSV
    # (this chart reuses films_worldwide + films_genre), so this is fact-only.
    def _top10(measure: str) -> pd.DataFrame:
        return con.execute(f"""
            WITH us AS (SELECT title, release_year FROM films_genre WHERE is_us=TRUE)
            SELECT w.title, g.primary_genre, w.{measure} AS value
            FROM films_worldwide w
            JOIN us ON us.title=w.title AND us.release_year=w.release_year
            JOIN films_genre g ON g.title=w.title AND g.release_year=w.release_year
            ORDER BY w.{measure} DESC LIMIT 10""").df()

    dom10 = _top10("domestic_gross")
    intl10 = _top10("foreign_gross")
    check("chart4: domestic top-10 has 10 rows", len(dom10) == 10, f"got {len(dom10)}")
    check("chart4: international top-10 has 10 rows", len(intl10) == 10, f"got {len(intl10)}")
    check(
        "chart4: top domestic film is Star Wars: The Force Awakens (~$937M)",
        dom10.iloc[0].title == "Star Wars: Episode VII - The Force Awakens"
        and approx(float(dom10.iloc[0].value), 936_662_225),
        f"got {dom10.iloc[0].title!r} @ {dom10.iloc[0].value:,}",
    )
    check(
        "chart4: top international film is Avatar (~$2.14B)",
        intl10.iloc[0].title == "Avatar" and approx(float(intl10.iloc[0].value), 2_138_489_059),
        f"got {intl10.iloc[0].title!r} @ {intl10.iloc[0].value:,}",
    )
    # The story is the DIFFERENCE between the two lists — lock in the membership
    # split so a data shift that quietly merges the lists gets caught.
    dset, iset = set(dom10.title), set(intl10.title)
    dom_only = dset - iset
    intl_only = iset - dset
    check(
        "chart4: domestic-only films are exactly {Black Panther, Top Gun: Maverick, No Way Home}",
        dom_only == {"Black Panther", "Top Gun: Maverick", "Spider-Man: No Way Home"},
        f"got {sorted(dom_only)}",
    )
    check(
        "chart4: international-only films are exactly {Furious 7, The Lion King, Zootopia 2}",
        intl_only == {"Furious 7", "The Lion King", "Zootopia 2"},
        f"got {sorted(intl_only)}",
    )
    check(
        "chart4: shared scale is honest — top domestic < smallest international bar",
        float(dom10.value.max()) < float(intl10.value.min()),
        f"top domestic {dom10.value.max():,} vs min international {intl10.value.min():,}",
    )
    # Every displayed film must have a genre (drives the color); no nulls.
    check(
        "chart4: all displayed films have a primary_genre",
        not dom10.primary_genre.isna().any() and not intl10.primary_genre.isna().any(),
        "a displayed film has no genre",
    )

    # ── Published CSVs match the DuckDB source (no drift) ─────────────────
    export_specs = [
        ("highest_grossing_films_v1.csv", adj, ["title", "adjusted_gross", "nominal_gross"]),
        ("films_worldwide_v1.csv", ww, ["title", "worldwide_gross", "domestic_gross", "foreign_gross"]),
        ("films_foreign_us_v1.csv", fl, ["title", "domestic_gross", "origin_name"]),
    ]
    for fname, df_db, cols in export_specs:
        path = export_dir / fname
        if not path.exists():
            check(f"export: {fname} exists", False, "missing export file")
            continue
        df_csv = pd.read_csv(path)
        # Compare on the sorted key columns so row order can't cause a false fail.
        # Compare VALUES, not dtypes: DuckDB nullable Int64 reads back as float64
        # from CSV, which is not a real difference. Numeric cols are compared with
        # a tolerance; text cols exactly.
        try:
            a = df_db[cols].sort_values(cols).reset_index(drop=True)
            b = df_csv[cols].sort_values(cols).reset_index(drop=True)
            same = a.shape == b.shape
            detail = ""
            if same:
                for c in cols:
                    if pd.api.types.is_numeric_dtype(a[c]):
                        # NaN-safe numeric equality within 1 unit (dollar figures)
                        diff = (a[c].astype("float64") - b[c].astype("float64")).abs()
                        col_ok = bool(((diff <= 1) | (a[c].isna() & b[c].isna())).all())
                    else:
                        # NaN-safe text compare (fill nulls with a sentinel so
                        # missing values on both sides count as equal).
                        av = a[c].fillna("\x00").astype(str)
                        bv = b[c].fillna("\x00").astype(str)
                        col_ok = bool((av == bv).all())
                    if not col_ok:
                        same = False
                        detail = f"column {c!r} differs"
                        break
            else:
                detail = f"row count {a.shape[0]} vs {b.shape[0]}"
            check(f"export: {fname} matches DuckDB on {cols}", same,
                  (detail + " — regenerate 03-prepare") if detail else
                  "CSV differs from the source table — regenerate 03-prepare")
        except KeyError as e:
            check(f"export: {fname} has expected columns {cols}", False, str(e))

    con.close()

    # ── Social vs web chart parity (when rendered outputs are present) ────
    # Each published chart must exist in BOTH the social set (outputs/social,
    # for Bluesky/X) and the web set (outputs/web, for the project page), and the
    # web charts must be the wider web canvas. Skipped on a fresh checkout where
    # outputs/ (gitignored) hasn't been regenerated.
    social = sorted((PROJECT / "outputs" / "social").glob("*.png"))
    web_dir = PROJECT / "outputs" / "web"
    if social and web_dir.exists():
        s_names = {p.name for p in social}
        w_names = {p.name for p in web_dir.glob("*.png")}
        check("social and web sets cover the same filenames", s_names == w_names,
              f"only social: {sorted(s_names - w_names)}; only web: {sorted(w_names - s_names)}")
        try:
            from PIL import Image
            dims = {Image.open(p).size for p in web_dir.glob("*.png")}
            check("every web chart is the web canvas 1664x936", dims == {(1664, 936)},
                  f"unexpected: {sorted(dims)}")
        except ImportError:
            pass

    # ── Report ────────────────────────────────────────────────────────────
    print("Pre-publish chart-data validation — highest-grossing-films")
    print("=" * 60)
    for line in checks:
        print(line)
    for line in failures:
        print(line)
    print("=" * 60)
    if failures:
        print(f"RESULT: {len(failures)} FAILURE(S) — DO NOT PUBLISH.")
        return 1
    print(f"RESULT: all {len(checks)} checks passed — safe to publish.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

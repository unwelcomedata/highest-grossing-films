# highest-grossing-films — Dataset Codebook
Generated: 2026-09-07

## Columns

### `rank_foreign`
- **Type**: `int32`
- **Non-null**: 100 / 100 (100.0%)
- **Description**: Rank among foreign-language films by U.S. & Canada gross (1 = highest).

### `title`
- **Type**: `str`
- **Non-null**: 100 / 100 (100.0%)
- **Description**: Film title.

### `domestic_gross_nominal`
- **Type**: `int64`
- **Non-null**: 100 / 100 (100.0%)
- **Description**: U.S. & Canada lifetime gross in year-of-release dollars, as reported (USD).

### `domestic_gross`
- **Type**: `int64`
- **Non-null**: 100 / 100 (100.0%)
- **Description**: U.S. & Canada lifetime gross restated in CONSTANT 2026 dollars using CPI-U (USD).

### `release_year`
- **Type**: `int32`
- **Non-null**: 100 / 100 (100.0%)
- **Description**: Year of original theatrical release.

### `distributor`
- **Type**: `str`
- **Non-null**: 100 / 100 (100.0%)
- **Description**: U.S. distributor as listed by Box Office Mojo.

### `origin_country`
- **Type**: `str`
- **Non-null**: 98 / 100 (98.0%)
- **Description**: Country-of-origin code (TMDB).

### `origin_name`
- **Type**: `str`
- **Non-null**: 98 / 100 (98.0%)
- **Description**: Country-of-origin name (TMDB), shown under each title on the chart.

## Notes

Source: Box Office Mojo, Foreign Language chart (non-English-language films),
ranked by U.S. & Canada lifetime gross; country of origin joined from TMDB. Grosses restated to
constant 2026 dollars using U.S. CPI-U (BLS CPIAUCNS via FRED), same basis as highest_grossing_films_v1.
"Foreign" here means LANGUAGE (primary language not English), the cleanest available definition.
"This product uses the TMDB API but is not endorsed or certified by TMDB."

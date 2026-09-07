# highest-grossing-films — Dataset Codebook
Generated: 2026-09-07

## Columns

### `rank_adjusted`
- **Type**: `int32`
- **Non-null**: 200 / 200 (100.0%)
- **Description**: Rank by inflation-adjusted domestic gross (1 = highest).

### `title`
- **Type**: `str`
- **Non-null**: 200 / 200 (100.0%)
- **Description**: Film title.

### `adjusted_gross_bom`
- **Type**: `int64`
- **Non-null**: 200 / 200 (100.0%)
- **Description**: Box Office Mojo's own ticket-price-adjusted gross (2022 $ base) - kept for reference only; NOT the published basis.

### `nominal_gross`
- **Type**: `int64`
- **Non-null**: 200 / 200 (100.0%)
- **Description**: Domestic lifetime gross in year-of-release dollars, as originally reported (USD).

### `est_tickets`
- **Type**: `int64`
- **Non-null**: 200 / 200 (100.0%)
- **Description**: Estimated number of tickets sold over the film lifetime (Box Office Mojo estimate).

### `release_year`
- **Type**: `int32`
- **Non-null**: 200 / 200 (100.0%)
- **Description**: Year of the film original theatrical release.

### `decade`
- **Type**: `int32`
- **Non-null**: 200 / 200 (100.0%)
- **Description**: Release decade (release_year rounded down to the nearest 10).

### `adjusted_gross`
- **Type**: `int64`
- **Non-null**: 200 / 200 (100.0%)
- **Description**: Domestic (U.S. & Canada) lifetime gross restated in CONSTANT 2026 dollars using CPI-U (USD).

### `inflation_multiple`
- **Type**: `float64`
- **Non-null**: 200 / 200 (100.0%)
- **Description**: adjusted_gross / nominal_gross - how many times its original take the CPI-U figure represents.

## Notes

Source: Box Office Mojo, Top Lifetime Grosses (domestic, US/Canada); nominal grosses restated to
constant 2026 dollars using U.S. CPI-U (BLS series CPIAUCNS, via FRED), trailing-12-month base.
URL: https://www.boxofficemojo.com/chart/top_lifetime_gross/
Method: adjusted_gross = nominal_gross * CPI(2026 TTM base) / CPI(release year). This is GENERAL
inflation (CPI-U), NOT Box Office Mojo's ticket-price adjustment (which only offers a 2022 base and
no foreign version). adjusted_gross_bom is retained for reference but is not the published figure.
Domestic only. Lifetime totals include re-release grosses, which inflates some classics.

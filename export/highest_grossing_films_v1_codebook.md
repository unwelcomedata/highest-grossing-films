# highest-grossing-films — Dataset Codebook
Generated: 2026-09-07

## Columns

### `rank_adjusted`
- **Type**: `int32`
- **Non-null**: 200 / 200 (100.0%)
- **Description**: Rank by ticket-price-adjusted domestic gross (1 = highest).

### `title`
- **Type**: `str`
- **Non-null**: 200 / 200 (100.0%)
- **Description**: Film title.

### `adjusted_gross`
- **Type**: `int64`
- **Non-null**: 200 / 200 (100.0%)
- **Description**: Domestic (U.S. & Canada) lifetime gross, adjusted for ticket-price inflation via Box Office Mojo (estimated tickets x today's average ticket price) - an admissions basis (USD).

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

### `inflation_multiple`
- **Type**: `float64`
- **Non-null**: 200 / 200 (100.0%)
- **Description**: adjusted_gross / nominal_gross - how many times its original take the adjusted figure represents.

## Notes

Source: Box Office Mojo, Top Lifetime Adjusted Grosses (domestic, US/Canada).
URL: https://www.boxofficemojo.com/chart/top_lifetime_gross_adjusted/?adjust_gross_to=2022
Method: adjusted_gross is Box Office Mojo's ticket-price adjustment - estimated tickets sold x a
reference-year average ticket price, i.e. an ADMISSIONS basis (counts people through the door), the
sound way to compare films across eras. NOT a CPI/general-inflation recalculation (a CPI version was
tried and reverted because it overstates old films unevenly by era). Domestic only; lifetime totals
include re-release grosses, which inflates some classics.

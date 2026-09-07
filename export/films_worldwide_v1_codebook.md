# highest-grossing-films — Dataset Codebook
Generated: 2026-09-07

## Columns

### `rank_worldwide`
- **Type**: `int32`
- **Non-null**: 200 / 200 (100.0%)
- **Description**: Rank by worldwide lifetime gross (1 = highest).

### `title`
- **Type**: `str`
- **Non-null**: 200 / 200 (100.0%)
- **Description**: Film title.

### `worldwide_gross`
- **Type**: `int64`
- **Non-null**: 200 / 200 (100.0%)
- **Description**: Worldwide lifetime gross, nominal USD (domestic + foreign).

### `domestic_gross`
- **Type**: `Int64`
- **Non-null**: 197 / 200 (98.5%)
- **Description**: Domestic (U.S. & Canada) lifetime gross, nominal USD.

### `foreign_gross`
- **Type**: `int64`
- **Non-null**: 200 / 200 (100.0%)
- **Description**: International (rest-of-world) lifetime gross, nominal USD.

### `release_year`
- **Type**: `int32`
- **Non-null**: 200 / 200 (100.0%)
- **Description**: Year of original theatrical release.

### `domestic_pct`
- **Type**: `float64`
- **Non-null**: 197 / 200 (98.5%)
- **Description**: Domestic gross as a percent of worldwide.

### `foreign_pct`
- **Type**: `float64`
- **Non-null**: 200 / 200 (100.0%)
- **Description**: International gross as a percent of worldwide.

## Notes

Source: Box Office Mojo, Top Lifetime Grosses (Worldwide).
Nominal (year-of-release) dollars, NOT inflation-adjusted. Domestic = US & Canada.

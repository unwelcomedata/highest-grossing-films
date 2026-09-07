# Sources

## Box Office Mojo — Top Lifetime Adjusted Grosses (Domestic)

- **Publisher:** Box Office Mojo (an IMDb / Amazon company).
- **URL:** https://www.boxofficemojo.com/chart/top_lifetime_gross_adjusted/?adjust_gross_to=2022
- **Retrieved:** 2026-09-06
- **Coverage:** Top domestic (U.S. & Canada) lifetime grosses, with Box Office
  Mojo's ticket-price adjustment.
- **Fields used:** rank, title, adjusted ("Adj. Lifetime") gross, nominal
  ("Lifetime") gross, estimated tickets sold, release year.
- **How it's used here:** the basis for **chart 2** (top domestic films, adjusted
  for inflation). The **published adjusted figure is Box Office Mojo's own
  ticket-price adjustment** — an admissions basis — not a CPI recalculation.

### Collection method

Box Office Mojo compiles theatrical box-office receipts reported by studios and
industry sources. "Domestic" means the United States and Canada. A film's
**lifetime** total includes all of its theatrical runs — original release plus any
re-releases.

### How the adjustment is defined (important)

The adjusted gross is **ticket-price inflation**, not CPI. Box Office Mojo
estimates the number of tickets a film sold over its lifetime and multiplies that
by a reference-year average ticket price. It is effectively an **admissions**
ranking dressed in dollars — it counts people through the door, which is the
sound way to compare films across very different eras.

**Why not CPI?** An earlier version of this project restated grosses with CPI-U
(general inflation) to get one basis across all charts. That was reverted:
ticket prices have risen much faster than general CPI, so CPI-adjusting old
grosses **overstates old films unevenly by era** (it pushed *Gone with the Wind*
to ~$4.7B and bunched the board together). Ticket-price/admissions is the honest,
standard method, so the project uses Box Office Mojo's published adjusted figure.

### Definitions / caveats

- **Nominal vs adjusted.** Nominal ("Lifetime") gross is in year-of-release
  dollars; a 1939 nominal figure and a 2019 nominal figure cannot be compared
  directly. The adjusted column exists to make the cross-era comparison possible.
- **Estimated tickets are modeled.** The adjustment rests on an estimate of
  tickets sold (gross ÷ era average price where actual admissions are
  unavailable), so it carries that estimation error.
- **Re-releases inflate some classics.** *Gone with the Wind*, *Star Wars*, and
  *E.T.* were re-released theatrically multiple times; their lifetime totals (and
  estimated tickets) accumulate across those runs — reflecting total historical
  theatrical audience, not a single release.
- **Domestic only.** No international box office is included in this chart.

### Licensing / attribution

Box Office Mojo data is © IMDb / Amazon. It is used here for commentary and
analysis with attribution. No Box Office Mojo content is redistributed beyond the
derived summary figures in this project's export; the published dataset is a
transformed analytical table, credited to the source above.

**No crowd-edited sources (e.g. Wikipedia) are used.**

---

## Box Office Mojo — Top Lifetime Grosses (Worldwide)

- **Publisher:** Box Office Mojo (IMDb / Amazon).
- **URL:** https://www.boxofficemojo.com/chart/ww_top_lifetime_gross/
- **Retrieved:** 2026-09-06
- **Coverage:** Top films by worldwide lifetime gross.
- **Fields used:** rank, title, worldwide / domestic / foreign lifetime gross,
  domestic %, foreign %, release year.
- **How it's used here:** basis for **chart 1** (home vs abroad), restricted to
  U.S.-produced films via TMDB origin country.

### Collection method

Studio-reported theatrical receipts. **Domestic = United States & Canada;
foreign = everywhere else.** Lifetime totals include all theatrical runs.

### Definitions / caveats

- **Nominal dollars.** These figures are *not* inflation-adjusted. Chart 1 shows
  each film's *share* earned home vs abroad, so the split is unaffected by
  inflation.
- **Foreign totals are noisy for some films.** Currency conversion and reporting
  completeness vary by market and era.
- **China-heavy films** (e.g. *Ne Zha 2*, *The Battle at Lake Changjin*, *Wolf
  Warrior 2*) can post enormous worldwide totals with near-zero domestic gross —
  a real signal, not an error. They are excluded from chart 1 because "domestic"
  (U.S. & Canada) is not their home market.
- **Figures are a snapshot as of the retrieval date (2026-09-06).** Films still in
  theatrical release when the data was pulled (e.g. 2026 titles like *Spider-Man:
  Brand New Day* and *The Odyssey*) have **incomplete lifetime totals that will
  keep climbing**. Any chart or post carries an "as-of Sep 2026" note, and
  in-release films should be read as lower bounds, not final.

---

## Box Office Mojo — Foreign Language chart

- **Publisher:** Box Office Mojo (IMDb / Amazon).
- **URL:** https://www.boxofficemojo.com/genre/sg4208980225/
- **Retrieved:** 2026-09-06
- **Coverage:** Non-English-language films by U.S. & Canada (domestic) lifetime
  gross.
- **Fields used:** title, domestic lifetime gross, release year.
- **How it's used here:** basis for **chart 3** — which foreign-*language* films
  earned the most in the U.S. Grosses are **nominal** (year-of-release dollars);
  there is no reliable admissions/ticket-price adjustment for this list, so it is
  shown nominal. Country of origin is joined from TMDB (below).

### Definitions / caveats

- **"Foreign" here means language, not nationality.** This is the cleanest,
  best-defined lens: a film is on this chart if its primary language is not
  English. (Country-of-origin and "non-Hollywood studio" proxies were explored
  during development but are noisier — origin is dominated by UK co-productions,
  and studio data is uneven — so language is the only basis published.)
- **Nominal dollars.** Figures are year-of-release dollars, so older titles are
  modestly understated relative to recent ones. Unlike chart 2 (which uses Box
  Office Mojo's ticket-price adjustment), there is no admissions adjustment
  published for the foreign-language list, so nominal is shown with this caveat
  noted on the chart itself.

---

## TMDB (The Movie Database) — country of origin

- **Publisher:** TMDB, https://www.themoviedb.org/
- **Retrieved:** 2026-09-06
- **Use:** **country of origin** per film, matched by title + release year. Two
  roles: (1) the derived `is_us` flag restricts chart 1 (home vs abroad) to
  U.S.-produced films so "home" means the same market for every film; (2) the
  origin-country label appears under each title in chart 3 (foreign-language).

### Why origin country matters (the "domestic" fix)

Box Office Mojo's "domestic" = **U.S. & Canada**, which is only a film's *home*
market for U.S.-made films. A Chinese blockbuster like *Ne Zha 2* earned ~$2.3B
almost entirely in China, but that shows up as "foreign" — making it look like a
film that conquered the world when it conquered its home market. Restricting the
home-vs-abroad chart to U.S.-produced films (`is_us = TRUE`) keeps that comparison
honest.

### Method & caveats

- **Origin is TMDB's `origin_country`** from the movie-detail endpoint; the derived
  `is_us` flag is true when the U.S. is among a film's origin countries.
- **Co-productions are fuzzy.** A film financed across several countries can carry
  multiple origin countries; the flag is a reasonable but not authoritative call.

### Licensing / attribution

"This product uses the TMDB API but is not endorsed or certified by TMDB." Metadata
is used for non-commercial analysis with attribution. The TMDB API key is stored
locally in a gitignored `.env` and is never committed.

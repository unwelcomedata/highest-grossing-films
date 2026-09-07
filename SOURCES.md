# Sources

## Box Office Mojo — Top Lifetime Grosses (Domestic)

- **Publisher:** Box Office Mojo (an IMDb / Amazon company).
- **URL:** https://www.boxofficemojo.com/chart/top_lifetime_gross/
- **Retrieved:** 2026-09-06
- **Coverage:** Top domestic (U.S. & Canada) lifetime grosses.
- **Fields used:** rank, title, nominal ("Lifetime") gross, release year.
- **How it's used here:** this is the basis for **chart 2** (top domestic films,
  inflation-adjusted). The nominal lifetime gross is restated into constant 2026
  dollars using CPI-U (see the CPI-U source below) — *not* Box Office Mojo's own
  ticket-price-adjusted figure.

### Collection method

Box Office Mojo compiles theatrical box-office receipts reported by studios and
industry sources. "Domestic" means the United States and Canada. A film's
**lifetime** total includes all of its theatrical runs — original release plus any
re-releases.

### Definitions / caveats

- **Nominal dollars.** The raw figures are in year-of-release dollars; a 1939
  figure and a 2019 figure cannot be compared directly. The CPI-U adjustment (next
  section) exists precisely to make that cross-era comparison possible.
- **Re-releases inflate some classics.** *Gone with the Wind*, *Star Wars*, and
  *E.T.* were re-released theatrically multiple times; their lifetime totals
  accumulate across those runs. This is part of why they top the adjusted board —
  it reflects total historical theatrical audience, not a single release.
- **Domestic only.** No international box office is included in this chart.

### Licensing / attribution

Box Office Mojo data is © IMDb / Amazon. It is used here for commentary and
analysis with attribution. No Box Office Mojo content is redistributed beyond the
derived summary figures in this project's export; the published dataset is a
transformed analytical table, credited to the source above.

**No crowd-edited sources (e.g. Wikipedia) are used.**

---

## U.S. CPI-U — inflation adjustment (via FRED)

- **Publisher:** U.S. Bureau of Labor Statistics (BLS), Consumer Price Index for
  All Urban Consumers (CPI-U), all items, U.S. city average, not seasonally
  adjusted — series **CPIAUCNS**.
- **URL:** https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCNS
  (FRED, Federal Reserve Bank of St. Louis, mirroring the BLS series).
- **Retrieved:** 2026-09-06
- **Use:** convert every film's nominal lifetime gross into **constant 2026
  dollars**, so films from 1937 and 2019 are on one comparable scale. Applied to
  charts 2 (domestic) and 3 (foreign-language).

### Method — why CPI-U, and how

- **General inflation, one consistent basis.** Each film's nominal gross is
  multiplied by `CPI(base) / CPI(release year)`, where the **base** is a
  trailing-12-month average of CPI-U (12 months to mid-2026) — i.e. "today's
  dollars," constant 2026 $. The same basis is used for both the domestic and the
  foreign-language chart, so the two are directly comparable.
- **Why not Box Office Mojo's adjusted chart?** BOM publishes a *ticket-price*
  adjustment, but only to a **2022** base and only for domestic films — there is
  no foreign-language adjusted version. To keep one honest, consistent method
  across every chart, this project uses CPI-U instead. The figures therefore
  **differ from BOM's adjusted chart on purpose**, and that is stated plainly
  rather than blended.
- **CPI vs ticket-price inflation.** These are different measures. Ticket prices
  have risen faster than the broad CPI in some decades, so a ticket-price
  adjustment produces a somewhat different — usually higher — ranking for old
  films than CPI does. CPI answers "what is this gross worth in today's general
  dollars," not "how many tickets did it sell."
- **Why FRED, not the BLS API.** The BLS public API v1 (no key) only returns the
  most recent ~3 years, insufficient for films back to 1937. The FRED CSV mirror
  of CPIAUCNS covers the full history. The monthly series is cached locally so
  re-runs are offline-safe.

### Licensing

U.S. government data, public domain. FRED redistributes the BLS series;
attribution to BLS / FRED.

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
  earned the most in the U.S. Grosses are restated to constant 2026 dollars
  (CPI-U). Country of origin is joined from TMDB (below).

### Definitions / caveats

- **"Foreign" here means language, not nationality.** This is the cleanest,
  best-defined lens: a film is on this chart if its primary language is not
  English. (Country-of-origin and "non-Hollywood studio" proxies were explored
  during development but are noisier — origin is dominated by UK co-productions,
  and studio data is uneven — so language is the only basis published.)
- **Nominal → CPI-U.** As with chart 2, older titles are modestly understated
  before adjustment; the published chart uses constant 2026 dollars so eras are
  comparable.

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

# Sources

## Box Office Mojo — Top Lifetime Adjusted Grosses (domestic)

- **Publisher:** Box Office Mojo (an IMDb / Amazon company).
- **URL:** https://www.boxofficemojo.com/chart/top_lifetime_gross_adjusted/?adjust_gross_to=2022
- **Retrieved:** 2026-09-06
- **Coverage:** Top 200 films by inflation-adjusted domestic (U.S. & Canada) lifetime gross.
- **Fields used:** rank, title, adjusted lifetime gross, nominal ("Lifetime") gross,
  estimated number of tickets sold, release year.

### Collection method

Box Office Mojo compiles theatrical box-office receipts reported by studios and
industry sources. "Domestic" means the United States and Canada. A film's
**lifetime** total includes all of its theatrical runs, i.e. original release
plus any re-releases.

### How the adjustment is defined (important)

The adjusted gross is **ticket-price inflation**, not CPI. Box Office Mojo
estimates the number of tickets a film sold over its lifetime and multiplies that
by a chosen reference year's average ticket price. This release uses
**`adjust_gross_to=2022`**, so every adjusted figure is expressed in 2022 dollars
via the 2022 average ticket price.

This matters:

- Ticket-price inflation ≠ general (CPI) inflation. Ticket prices have risen
  faster than the broad CPI in some decades, so a CPI-based adjustment would
  produce a different — usually lower — ranking for old films. This project
  reports the ticket-price method because that is what the source publishes; it
  is stated plainly rather than blended with CPI.
- Because the method is *tickets sold × a single reference-year price*, it is
  effectively an **admissions** ranking dressed in dollars. That is arguably the
  fairest cross-era comparison (it counts people through the door), but it is a
  modeled estimate, not an audited figure.

### Methodology changes / series breaks

- **Nominal vs adjusted are not comparable across eras.** Nominal ("Lifetime")
  gross is in *year-of-release dollars*; a 1939 nominal figure and a 2019 nominal
  figure cannot be compared directly. The adjusted column exists precisely to make
  a cross-era comparison possible.
- **Re-releases inflate some classics.** Films like *Gone with the Wind*, *Star
  Wars*, and *E.T.* were re-released theatrically multiple times; their lifetime
  totals (and estimated tickets) accumulate across those runs. This is part of why
  they top the adjusted board — it reflects total historical theatrical audience,
  not a single release.
- **Domestic only.** No international box office is included. Worldwide adjusted
  figures are unreliable for older films and are intentionally out of scope.
- **Estimated tickets are modeled.** Where actual admissions are unavailable, the
  ticket estimate is derived from gross ÷ the average ticket price for the film's
  era, so the adjustment carries that estimation error.

### Known controversies / caveats

- The "biggest movie ever" debate hinges entirely on the adjustment method.
  Nominal charts favor recent blockbusters (higher prices, more screens, IMAX/3D
  premiums); adjusted charts favor older films. Neither is "wrong" — they answer
  different questions. This project shows both, side by side, so the reader sees
  the gap rather than a single contested number.
- Average-ticket-price series themselves are estimates that vary by source; small
  differences in the assumed price shift the adjusted totals.

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
- **Coverage:** Top 200 films by worldwide lifetime gross.
- **Fields used:** rank, title, worldwide / domestic / foreign lifetime gross,
  domestic %, foreign %, release year.

### Collection method

Studio-reported theatrical receipts. **Domestic = United States & Canada;
foreign = everywhere else.** Lifetime totals include all theatrical runs
(original + re-releases).

### Definitions / caveats

- **Nominal dollars.** These figures are *not* inflation-adjusted — they are in
  year-of-release dollars. The worldwide board therefore favors recent, wide-
  release films (more screens, higher prices, more international markets). This is
  the opposite lens from the domestic *adjusted* chart, and the contrast is the
  point of the project.
- **Foreign totals are noisy for some films.** Currency conversion and reporting
  completeness vary by market and era.
- **China-heavy films** (e.g. *Ne Zha 2*, *The Battle at Lake Changjin*, *Wolf
  Warrior 2*) can post enormous worldwide totals with near-zero domestic gross —
  a real signal, not an error.
- **Figures are a snapshot as of the retrieval date (2026-09-06).** Films still in
  theatrical release when the data was pulled (e.g. 2026 titles like *Spider-Man:
  Brand New Day* and *The Odyssey*) have **incomplete lifetime totals that will
  keep climbing**. Any chart or post must carry an "as-of 2026-09-06" note, and
  in-release films should be read as lower bounds, not final.

---

## TMDB (The Movie Database) — film genres & country of origin

- **Publisher:** TMDB, https://www.themoviedb.org/
- **Retrieved:** 2026-09-06
- **Use:** genre label(s) and **country of origin** per film, matched by title +
  release year. `primary_genre` is TMDB's first-listed genre; a film usually has
  several (e.g. *Avatar* = Science Fiction, Action, Adventure). `origin_country`
  and the derived `is_us` flag come from TMDB's movie-detail endpoint.
- **Match rate:** 321/321 films matched.

### Why origin country matters (the "domestic" fix)

Box Office Mojo's "domestic" = **U.S. & Canada**, which is only a film's *home*
market for U.S.-made films. A Chinese blockbuster like *Ne Zha 2* earned ~$2.3B
almost entirely in China, but that shows up as "foreign" — making it look like a
film that conquered the world when it conquered its home market. To keep the
home-vs-abroad comparison consistent, the domestic-vs-international and genre
charts are **restricted to U.S.-produced films** (`is_us = TRUE`). Non-U.S. films
remain in the dataset for a separate analysis.

### Method & caveats (genre analysis)

- **Genres are TMDB's editorial tags**, applied by their contributor community —
  a reasonable but not authoritative taxonomy.
- **Multi-genre attribution.** Each film's full domestic and foreign gross is
  attributed to *each* of its genres, so a film like *Avatar* contributes to
  Sci-Fi, Action, and Adventure alike. Grosses therefore **double-count across
  genre buckets**. The genre chart shows a **share** (fraction of a genre's total
  gross earned outside the U.S. & Canada), not a sum, so the double-counting is
  fine — but absolute per-genre dollar totals should not be summed as if mutually
  exclusive.
- **Sample is U.S.-made films from the box-office top lists** — all already-large
  hits. Read the genre chart as "*among big U.S. films*, what share of each
  genre's take comes from abroad," not "which genres travel" in general.
- **Small-genre noise.** The genre chart is restricted to genres with **10+
  films**; sparse genres (e.g. Mystery) are excluded.

### Licensing / attribution

"This product uses the TMDB API but is not endorsed or certified by TMDB." Genre
metadata is used for non-commercial analysis with attribution. The TMDB API key is
stored locally in a gitignored `.env` and is never committed.

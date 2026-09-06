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

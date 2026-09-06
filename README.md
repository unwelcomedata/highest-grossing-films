**[@unwelcomedata](https://unwelcomedata.github.io/highest-grossing-films/)** · data from public sources

# "Highest-grossing" depends entirely on how you count

Ask which films are the biggest ever and you'll get three different answers
depending on where and when you measure. This project lays the three lenses side
by side — **domestic vs. worldwide**, **nominal vs. inflation-adjusted**, and
**by genre** — because the disagreements between them are the interesting part.

**The findings:**

- **Hollywood's biggest films make most of their money abroad.** For nearly every
  top U.S.-produced film, the rest-of-world box office dwarfs the home (U.S. &
  Canada) take. *Avatar* made $785M at home and **$2.1B** abroad.
- **Adjust for inflation and the "biggest domestic film" is from 1939.** Measured
  in 2022 dollars, *Gone with the Wind* still tops the domestic chart (~$1.9B),
  ahead of *Star Wars* (1977) — the modern hits only lead the *nominal* board.

> **A note on "domestic."** Box Office Mojo's "domestic" means the **U.S. &
> Canada** market — which only equals a film's *home* market for U.S.-made films.
> So the home-vs-abroad charts here are **restricted to U.S.-produced films**.
> Non-U.S. blockbusters (e.g. China's *Ne Zha 2*, which grossed ~$2.3B almost
> entirely at home) would otherwise look like they "earned it all abroad" when
> they earned it in their own country. Those films are a separate story.

---

## 1. Hollywood's biggest films make most of their money abroad

Top 15 U.S.-produced films by worldwide gross, ordered by the share earned
abroad. Gold = home (U.S. & Canada), teal = rest of world — the teal segment
grows for the more internationally-dependent films.

![Home vs abroad, top US films](docs/02_worldwide_domestic_vs_international.png)

## 2. The biggest *domestic* films, adjusted for inflation

A different question entirely: within the U.S. & Canada, adjusted for ticket-price
inflation, who sold the most tickets? Gold = nominal (release-year $), teal =
adjusted to 2022 $.

![Domestic gross, adjusted vs nominal](docs/01_domestic_adjusted_vs_nominal.png)

---

## How it was measured

- **Worldwide / domestic / international** grosses are **nominal** (year-of-release
  dollars) from Box Office Mojo. Domestic = U.S. & Canada; international =
  everywhere else. Nominal dollars favor recent films (higher prices, more
  markets) — which is exactly why the adjusted domestic chart tells a different
  story.
- **The adjusted domestic chart** uses *ticket-price* inflation (estimated tickets
  sold × the 2022 average ticket price), not CPI. It effectively ranks by tickets
  sold. Classics' totals include decades of re-releases.
- **Genre & origin country** come from TMDB, matched by title + year. The
  home-vs-abroad and genre charts are restricted to **U.S.-produced films** (via
  TMDB's origin country) so "home" means the same market for every film. In the
  genre chart, each film's gross is attributed to *every* one of its genres, so
  grosses double-count across genres — fine, because the chart shows a **share**
  (fraction earned abroad) per genre, not a sum.

**Snapshot as of September 2026.** Box-office figures are lifetime-to-date; films
still in theaters when the data was pulled (some 2026 titles) have totals that
will keep rising, so treat those as lower bounds.

Full per-source detail, definitions, and caveats are in [SOURCES.md](SOURCES.md).

---

## The data

Published datasets are in [`export/`](export/):

- `highest_grossing_films_v1.csv` — domestic, inflation-adjusted top 200 (adjusted
  + nominal gross, tickets, year, inflation multiple).
- `films_worldwide_v1.csv` — worldwide top 200 with domestic / international split.
- `films_genre_v1.csv` — genre(s) per film (TMDB).

Each ships with a `*_codebook.md` describing every column.

---

## Sources & license

Box Office Mojo (domestic adjusted + worldwide) and TMDB (genres). Full
attribution and caveats in [SOURCES.md](SOURCES.md). "This product uses the TMDB
API but is not endorsed or certified by TMDB." No crowd-edited sources are used.

---

> **AI-Assisted Development**
> This project was built with the assistance of [Kiro](https://kiro.dev), an
> AI-powered development environment. All data-sourcing decisions, methodology
> choices, and published findings are the responsibility of the author. AI was
> used for code generation, data-pipeline construction, and research assistance —
> not for analysis conclusions or editorial judgment.

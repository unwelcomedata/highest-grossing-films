"""Web ingestion utilities.

Handles three source types:
  - html_table  : pandas read_html on a static page
  - html_scrape : BeautifulSoup for custom element extraction
  - csv / json  : direct download and save to data/raw

All raw files land in data/raw unchanged. Call load_config() once per notebook
to get paths and source definitions from config.yaml.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests
import yaml
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def load_config(config_path: str | Path = "config.yaml") -> dict[str, Any]:
    """Load project config.yaml and return it as a dict."""
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def raw_path(cfg: dict, filename: str) -> Path:
    """Return a Path inside data/raw, creating the directory if needed."""
    p = Path(cfg["paths"]["data_raw"]) / filename
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

_CACHE_DIR: Path | None = None


def _get_cache_dir(cfg: dict) -> Path:
    """Return the cache directory (data/raw by default)."""
    global _CACHE_DIR
    if _CACHE_DIR is None:
        _CACHE_DIR = Path(cfg["paths"]["data_raw"])
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR


def fetch_html(url: str, headers: dict | None = None, timeout: int = 30) -> str:
    """Fetch a URL and return the response text.

    Raises requests.HTTPError on non-2xx status.
    """
    hdrs = {**_DEFAULT_HEADERS, **(headers or {})}
    resp = requests.get(url, headers=hdrs, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def fetch_cached(
    url: str,
    filename: str,
    cfg: dict,
    max_age_hours: float = 24.0,
    headers: dict | None = None,
    timeout: int = 30,
) -> str:
    """Fetch a URL with local file caching.

    If a cached file exists and is younger than max_age_hours, returns its
    contents without making a network request. Otherwise fetches, saves to
    data/raw/{filename}, and returns the content.

    Args:
        url:            URL to fetch.
        filename:       Cache filename (saved in data/raw/).
        cfg:            Loaded config dict.
        max_age_hours:  Re-fetch if cache is older than this (0 = always fetch).
        headers:        Optional extra HTTP headers.
        timeout:        Request timeout in seconds.

    Returns:
        Response text (from cache or network).
    """
    cache_path = _get_cache_dir(cfg) / filename
    if cache_path.exists() and max_age_hours > 0:
        age_hours = (time.time() - cache_path.stat().st_mtime) / 3600
        if age_hours < max_age_hours:
            return cache_path.read_text(encoding="utf-8")

    text = fetch_html(url, headers=headers, timeout=timeout)
    cache_path.write_text(text, encoding="utf-8")
    return text


def fetch_with_retry(
    url: str,
    headers: dict | None = None,
    timeout: int = 30,
    max_retries: int = 3,
    rate_limit_seconds: float = 1.5,
) -> str:
    """Fetch a URL with rate limiting and exponential backoff on 429s.

    Args:
        url:                 URL to fetch.
        headers:             Optional extra HTTP headers.
        timeout:             Request timeout in seconds.
        max_retries:         Max retry attempts on 429/5xx.
        rate_limit_seconds:  Minimum delay between requests.

    Returns:
        Response text.

    Raises:
        requests.HTTPError after exhausting retries.
    """
    hdrs = {**_DEFAULT_HEADERS, **(headers or {})}
    time.sleep(rate_limit_seconds)

    for attempt in range(max_retries + 1):
        resp = requests.get(url, headers=hdrs, timeout=timeout)
        if resp.status_code == 429 or resp.status_code >= 500:
            if attempt < max_retries:
                wait = rate_limit_seconds * (2 ** attempt)
                print(f"  ⚠ {resp.status_code} on {url} — retrying in {wait:.0f}s")
                time.sleep(wait)
                continue
        resp.raise_for_status()
        return resp.text

    resp.raise_for_status()  # will raise on the last failed attempt
    return ""  # unreachable


def fetch_html_js(url: str, wait_selector: str | None = None, timeout: int = 30000) -> str:
    """Fetch a JS-rendered page using Playwright (headless Chromium).

    Use this when fetch_html() returns an empty or incomplete page.
    Requires: playwright install chromium

    Args:
        url:           Page URL.
        wait_selector: Optional CSS selector to wait for before returning HTML.
        timeout:       Playwright timeout in milliseconds.
    """
    from playwright.sync_api import sync_playwright  # lazy import

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(extra_http_headers=_DEFAULT_HEADERS)
        page.goto(url, timeout=timeout)
        if wait_selector:
            page.wait_for_selector(wait_selector, timeout=timeout)
        else:
            page.wait_for_load_state("networkidle", timeout=timeout)
        html = page.content()
        browser.close()
    return html


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def parse_html_table(html: str, table_index: int = 0) -> pd.DataFrame:
    """Extract a <table> from HTML by index and return it as a DataFrame.

    Cleans up column names: lowercase, spaces → underscores.
    """
    tables = pd.read_html(html)
    if not tables:
        raise ValueError("No tables found in the provided HTML.")
    if table_index >= len(tables):
        raise IndexError(
            f"table_index {table_index} out of range — page has {len(tables)} table(s)."
        )
    df = tables[table_index]
    df.columns = [
        str(c).strip().lower().replace(" ", "_").replace("-", "_")
        for c in df.columns
    ]
    return df


def parse_html_scrape(
    html: str,
    row_selector: str,
    field_map: dict[str, str],
) -> pd.DataFrame:
    """Scrape structured rows from HTML using CSS selectors.

    Args:
        html:          Raw HTML string.
        row_selector:  CSS selector that matches each "row" element.
        field_map:     Dict mapping output column name → CSS selector
                       relative to each row element.
                       Use '' (empty string) to get the row's own text.

    Example:
        parse_html_scrape(html, "tr.data-row", {"name": "td.name", "value": "td.val"})
    """
    soup = BeautifulSoup(html, "lxml")
    rows = soup.select(row_selector)
    records = []
    for row in rows:
        record: dict[str, str] = {}
        for col, selector in field_map.items():
            el = row.select_one(selector) if selector else row
            record[col] = el.get_text(" ", strip=True) if el else ""
        records.append(record)
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Download helpers
# ---------------------------------------------------------------------------

def download_file(url: str, dest: Path, headers: dict | None = None, timeout: int = 60) -> Path:
    """Stream-download a file (CSV, JSON, zip, etc.) to dest and return the path."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    hdrs = {**_DEFAULT_HEADERS, **(headers or {})}
    with requests.get(url, headers=hdrs, timeout=timeout, stream=True) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                f.write(chunk)
    return dest


# ---------------------------------------------------------------------------
# Source-driven ingest (reads config.yaml sources block)
# ---------------------------------------------------------------------------

def ingest_source(
    name: str,
    cfg: dict,
    save_raw: bool = True,
    js_wait_selector: str | None = None,
    row_selector: str | None = None,
    field_map: dict[str, str] | None = None,
    rate_limit_seconds: float = 1.0,
) -> pd.DataFrame:
    """Ingest a named source from config.yaml and return a DataFrame.

    Args:
        name:               Key under `sources:` in config.yaml.
        cfg:                Loaded config dict (from load_config()).
        save_raw:           If True, save the raw HTML/bytes to data/raw/.
        js_wait_selector:   Passed to fetch_html_js() if js_render is true.
        row_selector:       Required for html_scrape type.
        field_map:          Required for html_scrape type.
        rate_limit_seconds: Polite delay before fetching.
    """
    source = cfg["sources"][name]
    url: str = source["url"]
    source_type: str = source.get("type", "html_table")
    js_render: bool = source.get("js_render", False)
    table_index: int = source.get("table_index", 0)

    time.sleep(rate_limit_seconds)

    if source_type == "csv":
        dest = raw_path(cfg, f"{name}.csv")
        download_file(url, dest)
        return pd.read_csv(dest, encoding=cfg["settings"]["encoding"])

    if source_type == "json":
        dest = raw_path(cfg, f"{name}.json")
        download_file(url, dest)
        with open(dest, encoding=cfg["settings"]["encoding"]) as f:
            data = json.load(f)
        return pd.json_normalize(data)

    # HTML-based types
    html = fetch_html_js(url, wait_selector=js_wait_selector) if js_render else fetch_html(url)

    if save_raw:
        raw_path(cfg, f"{name}.html").write_text(html, encoding="utf-8")

    if source_type == "html_table":
        return parse_html_table(html, table_index=table_index)

    if source_type == "html_scrape":
        if row_selector is None or field_map is None:
            raise ValueError("html_scrape requires row_selector and field_map arguments.")
        return parse_html_scrape(html, row_selector, field_map)

    raise ValueError(f"Unknown source type '{source_type}'. Use: html_table, html_scrape, csv, json.")


# ---------------------------------------------------------------------------
# Environment / secrets (.env) — no python-dotenv dependency
# ---------------------------------------------------------------------------

def load_env(env_path: str | Path = ".env") -> dict[str, str]:
    """Load KEY=VALUE lines from a .env file into os.environ and return them.

    Ignores blank lines and comments. Does not overwrite already-set vars.
    Never logs values. The .env file is gitignored — keys stay local.
    """
    import os
    env: dict[str, str] = {}
    p = Path(env_path)
    if not p.exists():
        return env
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip()
        env[k] = v
        os.environ.setdefault(k, v)
    return env


# ---------------------------------------------------------------------------
# TMDB genre enrichment (cached + rate-limited)
# ---------------------------------------------------------------------------

_TMDB_BASE = "https://api.themoviedb.org/3"
_tmdb_genre_map: dict[int, str] | None = None


def _tmdb_cache_dir(cfg: dict) -> Path:
    d = Path(cfg["paths"]["data_raw"]) / "tmdb"
    d.mkdir(parents=True, exist_ok=True)
    return d


def tmdb_genre_map(api_key: str) -> dict[int, str]:
    """Return TMDB's genre id -> name mapping (fetched once, memoized)."""
    global _tmdb_genre_map
    if _tmdb_genre_map is None:
        resp = requests.get(
            f"{_TMDB_BASE}/genre/movie/list",
            params={"api_key": api_key}, timeout=20,
        )
        resp.raise_for_status()
        _tmdb_genre_map = {g["id"]: g["name"] for g in resp.json()["genres"]}
    return _tmdb_genre_map


def _safe_slug(title: str, year: int | None) -> str:
    import re
    s = re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_").lower()
    return f"{s}_{year or 'na'}"


def tmdb_lookup_movie(
    title: str,
    year: int | None,
    api_key: str,
    cfg: dict,
    rate_limit_seconds: float = 0.3,
) -> dict[str, Any]:
    """Look up a single film on TMDB by title (+year), with local JSON caching.

    Returns a dict: {title, year, tmdb_id, tmdb_title, genres (list[str]),
    primary_genre, matched (bool)}. Cached under data/raw/tmdb/ so re-runs are
    offline and don't re-hit the API.
    """
    cache_path = _tmdb_cache_dir(cfg) / f"{_safe_slug(title, year)}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    time.sleep(rate_limit_seconds)  # polite
    params = {"api_key": api_key, "query": title}
    if year:
        params["year"] = year
    resp = requests.get(f"{_TMDB_BASE}/search/movie", params=params, timeout=20)
    resp.raise_for_status()
    results = resp.json().get("results", [])

    gmap = tmdb_genre_map(api_key)
    if results:
        top = results[0]
        genres = [gmap.get(i) for i in top.get("genre_ids", []) if gmap.get(i)]
        rec = {
            "title": title, "year": year,
            "tmdb_id": top.get("id"),
            "tmdb_title": top.get("title"),
            "genres": genres,
            "primary_genre": genres[0] if genres else None,
            "matched": True,
        }
    else:
        rec = {
            "title": title, "year": year, "tmdb_id": None, "tmdb_title": None,
            "genres": [], "primary_genre": None, "matched": False,
        }
    cache_path.write_text(json.dumps(rec), encoding="utf-8")
    return rec


def tmdb_movie_country(
    tmdb_id: int,
    api_key: str,
    cfg: dict,
    rate_limit_seconds: float = 0.3,
) -> dict[str, Any]:
    """Fetch a film's country of origin from TMDB's movie detail endpoint.

    Uses GET /3/movie/{id}, returns {tmdb_id, origin_country (list[str]),
    production_countries (list[str]), is_us (bool)}. Cached per id under
    data/raw/tmdb/country_<id>.json so re-runs are offline.

    is_us = True when the U.S. is among the film's origin/production countries —
    used to keep the domestic-vs-international analysis to films for which
    "domestic" (U.S. & Canada box office) actually means the home market.
    """
    cache_path = _tmdb_cache_dir(cfg) / f"country_{tmdb_id}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    time.sleep(rate_limit_seconds)
    resp = requests.get(
        f"{_TMDB_BASE}/movie/{tmdb_id}",
        params={"api_key": api_key}, timeout=20,
    )
    resp.raise_for_status()
    d = resp.json()
    origin = d.get("origin_country", []) or []
    prod = [c.get("iso_3166_1") for c in d.get("production_countries", [])]
    rec = {
        "tmdb_id": tmdb_id,
        "origin_country": origin,
        "production_countries": prod,
        "is_us": ("US" in origin) or ("US" in prod),
    }
    cache_path.write_text(json.dumps(rec), encoding="utf-8")
    return rec


def tmdb_movie_companies(
    tmdb_id: int,
    api_key: str,
    cfg: dict,
    rate_limit_seconds: float = 0.3,
) -> dict[str, Any]:
    """Fetch a film's production companies from TMDB's movie detail endpoint.

    Uses GET /3/movie/{id}, returns {tmdb_id, companies (list[str] of names),
    company_countries (list[str] of ISO codes), has_us_studio (bool)}. Cached
    per id under data/raw/tmdb/companies_<id>.json so re-runs are offline.

    has_us_studio = True when any production company's origin_country is "US".
    This is the "made within the U.S./Hollywood film industry" proxy: it counts
    a film as U.S.-industry when a U.S.-registered studio co-produced it, which
    correctly pulls U.S.-financed co-productions (Harry Potter, Bond, The
    Odyssey) into Hollywood — unlike a country-of-origin field that follows
    production-company registration or filming location. It is a documented
    proxy, not a ground-truth "industry of origin" field, which does not exist
    in any public dataset.
    """
    cache_path = _tmdb_cache_dir(cfg) / f"companies_{tmdb_id}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    time.sleep(rate_limit_seconds)
    resp = requests.get(
        f"{_TMDB_BASE}/movie/{tmdb_id}",
        params={"api_key": api_key}, timeout=20,
    )
    resp.raise_for_status()
    d = resp.json()
    companies = d.get("production_companies", []) or []
    names = [c.get("name") for c in companies if c.get("name")]
    ctys = [c.get("origin_country") for c in companies if c.get("origin_country")]
    rec = {
        "tmdb_id": tmdb_id,
        "companies": names,
        "company_countries": ctys,
        "has_us_studio": "US" in ctys,
    }
    cache_path.write_text(json.dumps(rec), encoding="utf-8")
    return rec


def fetch_cpi_annual(cfg: dict) -> "pd.DataFrame":
    """Fetch CPI-U (CPIAUCNS via FRED) and return ANNUAL AVERAGES, cached to raw.

    Returns a DataFrame [year:int, cpi:float, complete:bool] where cpi is the
    mean of that year's monthly CPI-U values and `complete` marks whether all 12
    months were present (the final year is usually partial). FRED's CPIAUCNS
    mirrors the BLS CPI-U (US city average, all items, not seasonally adjusted)
    back to 1913 and downloads as CSV without an API key — unlike the BLS public
    API v1, which without a registration key only returns ~3 recent years.

    Raw monthly CSV is cached to data/raw/cpi_cpiaucns_monthly.csv; the annual
    table to data/raw/cpi_annual.parquet. Used to convert nominal box office to
    constant "today's dollars" (latest COMPLETE annual CPI) on one basis.
    """
    from io import StringIO as _SIO

    monthly_cache = raw_path(cfg, "cpi_cpiaucns_monthly.csv")
    annual_cache = raw_path(cfg, "cpi_annual.parquet")
    if annual_cache.exists():
        return pd.read_parquet(annual_cache)

    if monthly_cache.exists():
        csv_text = monthly_cache.read_text(encoding="utf-8")
    else:
        url = cfg["sources"]["cpi"]["csv_url"]
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
        resp.raise_for_status()
        csv_text = resp.text
        monthly_cache.write_text(csv_text, encoding="utf-8")

    m = pd.read_csv(_SIO(csv_text))
    m.columns = ["date", "cpi"]
    m["date"] = pd.to_datetime(m["date"])
    m["year"] = m["date"].dt.year
    grp = m.groupby("year")["cpi"]
    annual = grp.mean().reset_index()
    annual["complete"] = (grp.count().values == 12)
    annual = annual.sort_values("year").reset_index(drop=True)

    # Trailing-12-month base for a genuine "today's dollars" reference. The NSA
    # CPI-U has a reporting lag / occasional missing month, so the latest
    # calendar year is usually incomplete; the mean of the most recent 12
    # available monthly readings is the most current honest base index. Stored
    # as DataFrame attrs (a scalar), so the per-year table stays integer-keyed
    # for joins.
    last12 = m.dropna(subset=["cpi"]).sort_values("date").tail(12)
    annual.attrs["ttm_cpi"] = float(last12["cpi"].mean())
    annual.attrs["ttm_end"] = f"{last12['date'].max():%Y-%m}"
    annual.attrs["ttm_complete"] = bool(len(last12) == 12)
    annual.to_parquet(annual_cache)
    return annual

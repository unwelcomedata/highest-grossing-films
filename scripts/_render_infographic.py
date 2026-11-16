"""Build + render the highest-grossing-films infographic (tall poster + 1600x900 social).

Every data-bearing mark (bar width, big number, label value) is COMPUTED here from
the project DuckDB (opened READ-ONLY, closed) -- nothing is eyeballed. Tall and
social renders are fed from the SAME computed values (one DATA dict). Each bar rect
carries data-sec / data-key / data-val / data-max / data-track attributes so
scripts/_validate_infographic.py can re-derive every mark independently.

Usage: .venv/bin/python scripts/_render_infographic.py
Outputs (docs/): infographic_films.svg/.png (tall), infographic_films_social.svg/.png
"""
from __future__ import annotations

from html import escape
from pathlib import Path

import duckdb

PROJECT = Path(__file__).resolve().parents[1]
DOCS = PROJECT / "docs"
DB = PROJECT / "data" / "project.duckdb"

NAVY, TEAL, CYAN, GOLD = "#003049", "#005F73", "#0A9396", "#EE9B00"
AQUA, VAN, GRAY, SILVER, CHAR = "#94D2BD", "#E9D8A6", "#6B7280", "#9CA3AF", "#1F2937"
BG = "#FBF8F0"
GENRE_COLORS = {  # same mapping as 06-viz-social chart 4
    "Science Fiction": "#003049", "Action": "#0A9396", "Animation": "#BB3E03",
    "Adventure": "#94D2BD", "Drama": "#EE9B00",
}
GENRE_SHORT = {"Science Fiction": "Sci-Fi"}

# Label text only (not data). Keyed by DB title.
SHORT = {  # social labels
    "Spider-Man: Brand New Day": "Spider-Man: Brand New Day",
    "Star Wars: Episode VII - The Force Awakens": "Star Wars: Force Awakens",
    "Avatar: The Way of Water": "Avatar: Way of Water",
    "Star Wars: Episode IV - A New Hope": "Star Wars: A New Hope",
    "E.T. the Extra-Terrestrial": "E.T. the Extra-Terrestrial",
    "Crouching Tiger, Hidden Dragon": "Crouching Tiger, Hidden Dragon",
}
FULL = {  # tall labels
    "Star Wars: Episode VII - The Force Awakens": "Star Wars: The Force Awakens",
    "Star Wars: Episode IV - A New Hope": "Star Wars: A New Hope",
}
SHORT4 = {  # S4 social, single-line
    "Spider-Man: Brand New Day": "Brand New Day",
    "Star Wars: Episode VII - The Force Awakens": "Force Awakens",
    "Avengers: Endgame": "Endgame", "Spider-Man: No Way Home": "No Way Home",
    "Avatar: The Way of Water": "Way of Water", "Avengers: Infinity War": "Infinity War",
}


def money(v: float) -> str:
    return f"${v/1e9:.2f}B" if v >= 1e9 else f"${v/1e6:.1f}M"


def load() -> dict:
    con = duckdb.connect(str(DB), read_only=True)
    try:
        ww = con.execute(
            "SELECT rank_worldwide, title, release_year, worldwide_gross, domestic_gross, "
            "foreign_gross, domestic_pct FROM films_worldwide ORDER BY worldwide_gross DESC"
        ).df()
        adj = con.execute(
            "SELECT title, release_year, adjusted_gross, nominal_gross FROM films_adjusted "
            "ORDER BY adjusted_gross DESC LIMIT 6"
        ).df()
        fl = con.execute(
            "SELECT title, release_year, domestic_gross, origin_name FROM films_foreign_us "
            "ORDER BY domestic_gross DESC LIMIT 10"
        ).df()

        def top10(measure: str):
            return con.execute(f"""
                WITH us AS (SELECT title, release_year FROM films_genre WHERE is_us=TRUE)
                SELECT w.title, w.release_year, g.primary_genre AS genre, w.{measure} AS value
                FROM films_worldwide w
                JOIN us ON us.title=w.title AND us.release_year=w.release_year
                JOIN films_genre g ON g.title=w.title AND g.release_year=w.release_year
                ORDER BY w.{measure} DESC LIMIT 10""").df()
        dom, intl = top10("domestic_gross"), top10("foreign_gross")
    finally:
        con.close()
    nz = ww[ww.title == "Ne Zha 2"].iloc[0]
    D = {
        "ww": ww.head(10).to_dict("records"),
        "adj": adj.to_dict("records"),
        "fl": fl.to_dict("records"),
        "dom": dom.to_dict("records"),
        "intl": intl.to_dict("records"),
        "nezha_ww_rank": int(nz.rank_worldwide),
    }
    D["fl_nezha_rank"] = 1 + [r["title"] for r in D["fl"]].index("Ne Zha 2")
    dt, it = {r["title"] for r in D["dom"]}, {r["title"] for r in D["intl"]}
    D["dom_only"] = [r["title"] for r in D["dom"] if r["title"] not in it]
    D["intl_only"] = [r["title"] for r in D["intl"] if r["title"] not in dt]
    return D


# ── small SVG helpers ────────────────────────────────────────────────────
def T(x, y, s, size, fill=CHAR, bold=False, anchor="start", extra=""):
    w = ' font-weight="bold"' if bold else ""
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" font-size="{size}"{w}{a}{extra}>{s}</text>'


def bar(x, y, h, val, vmax, track, fill, sec, key, series=""):
    w = val / vmax * track
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.2f}" height="{h}" fill="{fill}" '
            f'data-sec="{sec}" data-key="{escape(key)}" data-series="{series}" '
            f'data-val="{val}" data-max="{vmax}" data-track="{track}"/>'
            f"<!-- {escape(key)} {series} {val:,} / {vmax:,} x {track} -> {w:.2f} -->"), w


def legend(x_end, y, items, size):
    """Right-aligned legend of (color,label) built from the right edge."""
    out, x = [], x_end
    for color, label in reversed(items):
        tw = len(label) * size * 0.52
        x -= tw
        out.append(T(x, y, escape(label), size, GRAY))
        x -= size + 4
        out.append(f'<rect x="{x:.1f}" y="{y - size + 2:.1f}" width="{size - 2}" height="{size - 2}" fill="{color}"/>')
        x -= 18
    return out


def label(x, y, title, year, size, tall):
    name = escape(FULL.get(title, title) if tall else SHORT.get(title, title))
    ys = f'<tspan fill="{SILVER}" font-size="{size - 3}"> ({year})</tspan>' if tall else ""
    return T(x, y, f"{name}{ys}", size, CHAR)


# ── sections: each returns (elements, height). cfg = per-render sizes ────
def head(x, y, title, support, cfg):
    return [T(x, y + cfg["h1"], escape(title), cfg["h1"], NAVY, True),
            T(x, y + cfg["h1"] + cfg["h2"] + 10, escape(support), cfg["h2"], GRAY)]


def sec_ww(D, x, y, cfg):
    tall = cfg["tall"]
    el = head(x, y, "Top 10 worldwide: home vs abroad", cfg["s1_sup"], cfg)
    ly = y + cfg["h1"] + cfg["h2"] + 10
    LE = cfg["le"]
    el += legend(x + cfg["W"], ly + LE, [(TEAL, "U.S./Canada"), (GOLD, "International")], cfg["h2"] - (2 if tall else 1))
    vmax = max(r["worldwide_gross"] for r in D["ww"])
    cy = y + cfg["content"] + LE
    for i, r in enumerate(D["ww"]):
        ry = cy + i * cfg["row"]
        el.append(label(x, ry + cfg["bh"] - 4, r["title"], r["release_year"], cfg["fs"], tall))
        bx = x + cfg["lab"]
        b1, w1 = bar(bx, ry, cfg["bh"], r["domestic_gross"], vmax, cfg["track"], TEAL, "ww", r["title"], "domestic")
        b2, w2 = bar(bx + w1, ry, cfg["bh"], r["foreign_gross"], vmax, cfg["track"], GOLD, "ww", r["title"], "international")
        el += [b1, b2]
        el.append(T(x + cfg["W"], ry + cfg["bh"] - 4, f"{money(r['worldwide_gross'])} &#183; {r['domestic_pct']:.1f}% U.S.",
                    cfg["fs"] - 1, NAVY, True, "end"))
    return el, cfg["content"] + LE + len(D["ww"]) * cfg["row"]


def sec_adj(D, x, y, cfg):
    tall = cfg["tall"]
    el = head(x, y, "Domestic gross: as released vs. ticket-price adjusted", cfg["s2_sup"], cfg)
    ly = y + cfg["h1"] + cfg["h2"] + 10
    LE = cfg["le"]
    el += legend(x + cfg["W"], ly + LE, [(SILVER, "As released"), (TEAL, "Ticket-price adjusted")], cfg["h2"] - (2 if tall else 1))
    vmax = max(r["adjusted_gross"] for r in D["adj"])
    cy = y + cfg["content"] + LE
    bh = cfg["bh2"]
    for i, r in enumerate(D["adj"]):
        ry = cy + i * cfg["row2"]
        el.append(label(x, ry + bh + 3, r["title"], r["release_year"], cfg["fs"], tall))
        bx = x + cfg["lab"]
        b1, w1 = bar(bx, ry, bh, r["nominal_gross"], vmax, cfg["track2"], SILVER, "adj", r["title"], "nominal")
        b2, w2 = bar(bx, ry + bh + 3, bh, r["adjusted_gross"], vmax, cfg["track2"], TEAL, "adj", r["title"], "adjusted")
        el += [b1, b2]
        el.append(T(bx + w1 + 8, ry + bh - 2, money(r["nominal_gross"]), cfg["fs"] - 3, GRAY))
        el.append(T(bx + w2 + 8, ry + 2 * bh + 1, money(r["adjusted_gross"]), cfg["fs"] - 3, NAVY, True))
        mult = r["adjusted_gross"] / r["nominal_gross"]
        el.append(T(x + cfg["W"], ry + bh + 8, f"{mult:.1f}&#215;", cfg["fs"] + 4, TEAL, True, "end"))
    return el, cfg["content"] + LE + len(D["adj"]) * cfg["row2"]


def sec_fl(D, x, y, cfg):
    tall = cfg["tall"]
    el = head(x, y, "Foreign-language films by U.S. gross", cfg["s3_sup"], cfg)
    vmax = max(r["domestic_gross"] for r in D["fl"])
    cy = y + cfg["content"]
    for i, r in enumerate(D["fl"]):
        ry = cy + i * cfg["row"]
        el.append(label(x, ry + cfg["bh"] - 4, r["title"], r["release_year"], cfg["fs"], tall))
        bx = x + cfg["lab3"]
        nz = r["title"] == "Ne Zha 2"
        b, w = bar(bx, ry, cfg["bh"], r["domestic_gross"], vmax, cfg["track3"], GOLD if nz else CYAN, "fl", r["title"], "us_gross")
        el.append(b)
        txt = f"{money(r['domestic_gross'])} &#183; {escape(r['origin_name'])}"
        el.append(T(bx + w + 8, ry + cfg["bh"] - 4, txt, cfg["fs"] - 2, NAVY, True))
        if nz:
            el.append(T(bx + w + 8 + len(txt) * (cfg["fs"] - 2) * 0.5 + 10, ry + cfg["bh"] - 4,
                        f"also #{D['nezha_ww_rank']} worldwide", cfg["fs"] - 3, GOLD, True))
    return el, cfg["content"] + len(D["fl"]) * cfg["row"]


def sec_genre(D, x, y, cfg):
    tall = cfg["tall"]
    el = head(x, y, "Top 10 domestic vs. top 10 international", cfg["s4_sup"], cfg)
    ly = y + cfg["h1"] + cfg["h2"] + 10
    present = []
    for r in D["dom"] + D["intl"]:
        if r["genre"] not in present:
            present.append(r["genre"])
    leg = [(GENRE_COLORS[g], GENRE_SHORT.get(g, g)) for g in present]
    LE = cfg["le"]
    el += legend(x + cfg["W"], ly + LE, leg, cfg["h2"] - 2)
    vmax = max(r["value"] for r in D["dom"] + D["intl"])  # one shared scale
    cy = y + cfg["content"] + LE
    cols = [("By domestic gross", D["dom"], D["dom_only"]), ("By international gross", D["intl"], D["intl_only"])]
    for ci, (ttl, rows, only) in enumerate(cols):
        cx = x + ci * cfg["colx"]
        if tall:
            el.append(T(cx, cy + 4, ttl, 22, NAVY, True))
        base = cy + (34 if tall else 0)
        for i, r in enumerate(rows):
            ry = base + i * cfg["row4"]
            bold = tall and r["title"] in only
            if tall:
                el.append(T(cx, ry + 16, escape(FULL.get(r["title"], r["title"])) +
                            f'<tspan fill="{SILVER}" font-size="15" font-weight="normal"> ({r["release_year"]})</tspan>',
                            19, CHAR, bold))
                b, w = bar(cx, ry + 22, 16, r["value"], vmax, cfg["track4"], GENRE_COLORS[r["genre"]], "genre", r["title"], "domestic" if ci == 0 else "international")
                vx, vy = cx + w + 8, ry + 36
            else:
                el.append(T(cx, ry + 13, escape(SHORT4.get(r["title"], r["title"])), 13, CHAR))
                b, w = bar(cx + cfg["lab4"], ry + 3, 13, r["value"], vmax, cfg["track4"], GENRE_COLORS[r["genre"]], "genre", r["title"], "domestic" if ci == 0 else "international")
                vx, vy = cx + cfg["lab4"] + w + 5, ry + 13
            el.append(b)
            el.append(T(vx, vy, money(r["value"]), 15 if tall else 12, NAVY, True))
    h = cfg["content"] + LE + (34 if tall else 0) + 10 * cfg["row4"]
    if tall:
        d = ", ".join(escape(FULL.get(t, t)) for t in D["dom_only"])
        i_ = ", ".join(escape(FULL.get(t, t)) for t in D["intl_only"])
        el.append(T(x, y + h + 20, f"Bold = on that list only. Domestic only: {d}.", 18, GRAY))
        el.append(T(x, y + h + 46, f"International only: {i_}.", 18, GRAY))
        h += 56
    return el, h


def header_footer_tall(H, title_sz=76):
    return [
        f'<rect width="1200" height="{H}" fill="{BG}"/>',
        f'<rect x="0" y="0" width="1200" height="300" fill="{NAVY}"/>',
        T(80, 130, "Highest-Grossing Films", title_sz, "#FFFFFF", True),
        T(80, 190, "It depends on how you count", 40, AQUA, True),
        T(80, 240, "Box office through four lenses: worldwide, ticket-price adjusted, foreign-language, domestic vs. international.", 22, VAN),
        f'<rect x="0" y="{H - 90}" width="1200" height="90" fill="{NAVY}"/>',
        T(80, H - 45, "@unwelcomedata", 24, "#FFFFFF", True),
        T(80, H - 15, "Source: Box Office Mojo; genre via TMDB &#183; retrieved 2026-09-18 &#183; nominal $ unless noted &#183; 2026 releases still in theaters", 17, AQUA),
    ]


def build_tall(D) -> str:
    cfg = dict(tall=True, W=1040, h1=34, h2=22, content=100, fs=20, row=46, bh=28, lab=380, track=440,
               row2=74, bh2=26, track2=430, lab3=0, track3=0, row4=62, colx=540, lab4=0, track4=390, le=30,
               s1_sup="Bar length = worldwide gross; split = U.S./Canada (domestic) vs. everywhere else.",
               s2_sup="U.S./Canada lifetime gross, six top films by adjusted gross; right = adjusted / as released.",
               s3_sup="Ten highest U.S. grosses (nominal $) among foreign-language releases, with country of origin.",
               s4_sup="U.S.-produced films, one shared scale. Bar color = primary genre.")
    cfg["lab3"] = 380
    cfg["track3"] = 400
    body, y = [], 330
    divs = []
    for fn in (sec_ww, sec_adj, sec_fl, sec_genre):
        c = dict(cfg)
        el, h = fn(D, 80, y, c)
        body += el
        y += h + 30
        if fn is not sec_genre:
            divs.append(y - 15)
            y += 15
    H = int(y + 20 + 90)
    out = [f'<?xml version="1.0" encoding="UTF-8"?>',
           "<!-- highest-grossing-films infographic (tall). All data marks computed from data/project.duckdb by scripts/_render_infographic.py -->",
           f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{H}" viewBox="0 0 1200 {H}" font-family="Helvetica, Arial, sans-serif">']
    out += header_footer_tall(H)
    for d in divs:
        out.append(f'<line x1="80" y1="{d:.0f}" x2="1120" y2="{d:.0f}" stroke="{VAN}" stroke-width="3"/>')
    out += body + ["</svg>"]
    return "\n".join(out), H


def build_social(D) -> str:
    base = dict(tall=False, W=720, h1=25, h2=16, content=62, fs=15, row=21.5, bh=14, lab=210, track=315,
                row2=37.5, bh2=16, track2=300, lab3=240, track3=225, row4=22, colx=365, lab4=120, track4=178, le=0,
                s1_sup="Bar = worldwide gross; split = home vs. abroad.",
                s2_sup="U.S./Canada lifetime; right = adjusted / released.",
                s3_sup="Top 10 U.S. gross (nominal $), with country of origin.",
                s4_sup="Top 10 each (U.S.-produced), shared scale.")
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           "<!-- highest-grossing-films infographic (landscape social 1600x900). Same computed values as the tall render. -->",
           '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900" font-family="Helvetica, Arial, sans-serif">',
           f'<rect width="1600" height="900" fill="{BG}"/>',
           f'<rect x="0" y="0" width="1600" height="188" fill="{NAVY}"/>',
           T(80, 82, "Highest-Grossing Films", 52, "#FFFFFF", True),
           T(80, 128, "It depends on how you count", 30, AQUA, True),
           T(80, 162, "Box office through four lenses: worldwide, ticket-price adjusted, foreign-language, domestic vs. international.", 19, VAN),
           f'<line x1="800" y1="205" x2="800" y2="795" stroke="{VAN}" stroke-width="3"/>',
           f'<line x1="80" y1="500" x2="780" y2="500" stroke="{VAN}" stroke-width="3"/>',
           f'<line x1="820" y1="500" x2="1520" y2="500" stroke="{VAN}" stroke-width="3"/>']
    for fn, x, y in ((sec_ww, 80, 205), (sec_fl, 820, 205), (sec_adj, 80, 512), (sec_genre, 820, 512)):
        c = dict(base)
        if fn is sec_fl:
            c["lab"] = 240
        el, _ = fn(D, x, y, c)
        out += el
    out += [f'<rect x="0" y="810" width="1600" height="90" fill="{NAVY}"/>',
            T(80, 855, "@unwelcomedata", 24, "#FFFFFF", True),
            T(80, 885, "Source: Box Office Mojo; genre via TMDB &#183; retrieved 2026-09-18 &#183; nominal $ unless noted &#183; 2026 releases still in theaters", 17, AQUA),
            "</svg>"]
    return "\n".join(out)


def render(jobs) -> None:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for svg_name, png_name, w, h in jobs:
            svg = (DOCS / svg_name).read_text(encoding="utf-8")
            html = f"<!doctype html><html><head><style>*{{margin:0;padding:0}}</style></head><body>{svg}</body></html>"
            page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
            page.set_content(html)
            page.wait_for_timeout(300)
            page.screenshot(path=str(DOCS / png_name), clip={"x": 0, "y": 0, "width": w, "height": h})
            page.close()
            print(f"rendered {png_name} ({w}x{h})")
        browser.close()


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    D = load()
    tall, H = build_tall(D)
    (DOCS / "infographic_films.svg").write_text(tall, encoding="utf-8")
    (DOCS / "infographic_films_social.svg").write_text(build_social(D), encoding="utf-8")
    render([("infographic_films.svg", "infographic_films.png", 1200, H),
            ("infographic_films_social.svg", "infographic_films_social.png", 1600, 900)])


if __name__ == "__main__":
    main()

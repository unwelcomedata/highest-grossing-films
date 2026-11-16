"""Validate every data mark in both infographic SVGs back to source.

Independent of the render script's logic: re-queries DuckDB (read-only) and the
export CSVs, then checks each <rect data-sec=...> value, width (= val/max*track),
section max, and the printed big-number text, in BOTH renders. Exit 0 = no mismatch.
Usage: .venv/bin/python scripts/_validate_infographic.py
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import duckdb
import pandas as pd

P = Path(__file__).resolve().parents[1]
NS = "{http://www.w3.org/2000/svg}"
fails: list[str] = []
n_checked = 0


def chk(ok: bool, msg: str) -> None:
    global n_checked
    n_checked += 1
    if not ok:
        fails.append(msg)


def rects(path: Path):
    root = ET.parse(path).getroot()
    return [e.attrib for e in root.iter(NS + "rect") if "data-sec" in e.attrib], \
           ["".join(e.itertext()) for e in root.iter(NS + "text")]


def money(v):
    return f"${v/1e9:.2f}B" if v >= 1e9 else f"${v/1e6:.1f}M"


def main() -> int:
    con = duckdb.connect(str(P / "data/project.duckdb"), read_only=True)
    ww = con.execute("SELECT * FROM films_worldwide ORDER BY worldwide_gross DESC").df()
    adj = con.execute("SELECT * FROM films_adjusted ORDER BY adjusted_gross DESC").df()
    fl = con.execute("SELECT * FROM films_foreign_us ORDER BY domestic_gross DESC").df()

    def top10(m):
        return con.execute(f"""WITH us AS (SELECT title, release_year FROM films_genre WHERE is_us=TRUE)
            SELECT w.title, g.primary_genre genre, w.{m} v FROM films_worldwide w
            JOIN us ON us.title=w.title AND us.release_year=w.release_year
            JOIN films_genre g ON g.title=w.title AND g.release_year=w.release_year
            ORDER BY w.{m} DESC LIMIT 10""").df()
    dom, intl = top10("domestic_gross"), top10("foreign_gross")
    con.close()

    # export CSVs agree with DB for the figures used
    exp_w = pd.read_csv(P / "export/films_worldwide_v1.csv").set_index("title")
    exp_a = pd.read_csv(P / "export/highest_grossing_films_v1.csv").set_index("title")
    exp_f = pd.read_csv(P / "export/films_foreign_us_v1.csv").set_index("title")

    # expected marks: (sec, series) -> {key: val}, plus section max
    exp = {}
    w10 = ww.head(10)
    wmax = int(w10.worldwide_gross.max())
    exp[("ww", "domestic")] = dict(zip(w10.title, w10.domestic_gross))
    exp[("ww", "international")] = dict(zip(w10.title, w10.foreign_gross))
    a6 = adj.head(6)
    amax = int(a6.adjusted_gross.max())
    exp[("adj", "nominal")] = dict(zip(a6.title, a6.nominal_gross))
    exp[("adj", "adjusted")] = dict(zip(a6.title, a6.adjusted_gross))
    f10 = fl.head(10)
    fmax = int(f10.domestic_gross.max())
    exp[("fl", "us_gross")] = dict(zip(f10.title, f10.domestic_gross))
    gmax = int(max(dom.v.max(), intl.v.max()))
    exp[("genre", "domestic")] = dict(zip(dom.title, dom.v))
    exp[("genre", "international")] = dict(zip(intl.title, intl.v))
    secmax = {"ww": wmax, "adj": amax, "fl": fmax, "genre": gmax}

    # export-vs-DB for every value used
    for t, r in w10.set_index("title").iterrows():
        chk(int(exp_w.loc[t, "worldwide_gross"]) == r.worldwide_gross and int(exp_w.loc[t, "domestic_gross"]) == r.domestic_gross
            and int(exp_w.loc[t, "foreign_gross"]) == r.foreign_gross, f"export mismatch ww {t}")
        chk(r.domestic_gross + r.foreign_gross == r.worldwide_gross, f"split != total {t}")
    for t, r in a6.set_index("title").iterrows():
        chk(int(exp_a.loc[t, "adjusted_gross"]) == r.adjusted_gross and int(exp_a.loc[t, "nominal_gross"]) == r.nominal_gross, f"export mismatch adj {t}")
    for t, r in f10.set_index("title").iterrows():
        chk(int(exp_f.loc[t, "domestic_gross"]) == r.domestic_gross, f"export mismatch fl {t}")

    # validate_charts.py facts
    chk(ww.iloc[0].title == "Avatar", "top worldwide not Avatar")
    chk(adj.iloc[0].title == "Gone with the Wind" and abs(adj.iloc[0].adjusted_gross - 1_895_421_694) / 1_895_421_694 <= .005, "GWTW adjusted fact")
    chk(fl.iloc[0].title == "Crouching Tiger, Hidden Dragon" and abs(fl.iloc[0].domestic_gross - 128_078_872) / 128_078_872 <= .005, "Crouching Tiger fact")
    chk(dom.iloc[0].title == "Spider-Man: Brand New Day" and dom.iloc[0].v >= 937_441_963 * .995, "top domestic fact")
    chk(intl.iloc[0].title == "Avatar" and abs(intl.iloc[0].v - 2_138_489_059) / 2_138_489_059 <= .005, "top intl fact")
    chk(set(dom.title) - set(intl.title) == {"Black Panther", "Top Gun: Maverick", "Spider-Man: No Way Home"}, "domestic-only set")
    chk(set(intl.title) - set(dom.title) == {"Furious 7", "The Lion King", "Zootopia 2"}, "intl-only set")
    chk(int(ww[ww.title == "Ne Zha 2"].rank_worldwide.iloc[0]) == 5, "Ne Zha 2 worldwide rank 5")
    chk(list(f10.title).index("Ne Zha 2") == 9, "Ne Zha 2 foreign-language rank 10")

    fracs = {}
    for name in ("infographic_films.svg", "infographic_films_social.svg"):
        rs, texts = rects(P / "docs" / name)
        alltext = " | ".join(texts)
        seen = set()
        for a in rs:
            sec, ser, key = a["data-sec"], a["data-series"], a["data-key"]
            val, mx, tr, w = float(a["data-val"]), float(a["data-max"]), float(a["data-track"]), float(a["width"])
            e = exp[(sec, ser)].get(key)
            chk(e is not None, f"{name}: unexpected mark {sec}/{ser}/{key}")
            if e is None:
                continue
            chk(val == float(e), f"{name}: {sec}/{ser}/{key} val {val} != source {e}")
            chk(mx == secmax[sec], f"{name}: {sec} max {mx} != {secmax[sec]}")
            chk(abs(w - val / secmax[sec] * tr) <= 0.01, f"{name}: {sec}/{ser}/{key} width {w} != {val/secmax[sec]*tr:.2f}")
            fracs.setdefault((sec, ser, key), []).append(w / tr)
            seen.add((sec, ser, key))
            # printed labels
            if sec == "ww" and ser == "domestic":
                r = w10.set_index("title").loc[key]
                chk(f"{money(r.worldwide_gross)} · {r.domestic_pct:.1f}% U.S." in alltext, f"{name}: ww label {key}")
                chk(abs(r.domestic_pct - round(100 * r.domestic_gross / r.worldwide_gross, 1)) < 0.051, f"domestic_pct vs recompute {key}")
            if sec == "adj" and ser == "adjusted":
                r = a6.set_index("title").loc[key]
                chk(f"{r.adjusted_gross / r.nominal_gross:.1f}×" in alltext, f"{name}: multiple {key}")
                chk(money(r.adjusted_gross) in alltext and money(r.nominal_gross) in alltext, f"{name}: adj labels {key}")
            if sec == "fl":
                r = f10.set_index("title").loc[key]
                chk(f"{money(r.domestic_gross)} · {r.origin_name}" in alltext, f"{name}: fl label {key}")
            if sec == "genre":
                chk(money(val) in alltext, f"{name}: genre label {key}")
        want = {(s, se, k) for (s, se), d in exp.items() for k in d}
        chk(seen == want, f"{name}: missing marks {sorted(want - seen)[:3]}")
    # tall and social plot identical fractions of their tracks (SVG widths are rounded to 0.01px)
    for k, v in fracs.items():
        chk(len(v) == 2 and abs(v[0] - v[1]) < 5e-4, f"tall vs social fraction differs {k}: {v}")
    print(f"infographic data-mark validation: {n_checked} checks, {len(fails)} failures")
    for f in fails:
        print("  FAIL", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Hourly perp volume + open interest from DefiLlama -> data/volume.json (stdlib only)."""
import json, os, re, sys, urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "volume.json")
UA = {"User-Agent": "perp-maxing volume bot", "Accept": "application/json"}
API = "https://api.llama.fi"

# project id -> DefiLlama name patterns (regex, matched against name/displayName/slug)
MATCH = {
    "variational": r"\bvariational\b",
    "lighter": r"\blighter\b",
    "extended": r"\bextended\b",
    "risex": r"\brise ?x\b|\brise\b",
    "nado": r"\bnado\b",
    "entropy": r"\bentropy\b",
    "arcus": r"\barcus\b",
}


def get(path):
    req = urllib.request.Request(API + path, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


ERR = {}


def protocols(kind):
    for q in ("?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true", ""):
        try:
            d = get(f"/overview/{kind}{q}")
            rows = d.get("protocols", [])
            ERR[kind] = f"{len(rows)} rows"
            return rows
        except Exception as e:
            ERR[kind] = f"{type(e).__name__}: {e}"
    return []


def pick(rows, pattern):
    rx = re.compile(pattern, re.I)
    hits = [p for p in rows if any(rx.search(str(p.get(k) or "")) for k in ("name", "displayName", "slug"))]
    # prefer parent/aggregate rows with the most volume
    hits.sort(key=lambda p: (p.get("total24h") or 0), reverse=True)
    return hits


def main():
    now = datetime.now(timezone.utc)
    oi_rows = protocols("open-interest")
    out = {"updated": now.strftime("%Y-%m-%dT%H:%MZ"), "source": "DefiLlama", "projects": {}, "debug": {}}
    for pid, pat in MATCH.items():
        hits = pick(oi_rows, pat)
        out["debug"][pid] = [f'{h.get("displayName") or h.get("name")} [{h.get("slug")}] oi={h.get("total24h")}' for h in hits[:6]]
        if not hits:
            continue
        h = hits[0]
        slug = h.get("slug")
        rec = {"name": h.get("displayName") or h.get("name"), "slug": slug, "oi": h.get("total24h"),
               "oi_ch1d": h.get("change_1d"), "chains": h.get("chains"),
               "url": f"https://defillama.com/protocol/{slug}"}
        try:
            sm = get(f"/summary/derivatives/{slug}?dataType=dailyVolume")
            rec.update({"v24h": sm.get("total24h"), "v7d": sm.get("total7d"), "v30d": sm.get("total30d"),
                        "ch1d": sm.get("change_1d"), "ch7d": sm.get("change_7d"), "ch1m": sm.get("change_1m")})
            chart = sm.get("totalDataChart") or []
            rec["chart"] = [[int(t), round(float(v))] for t, v in chart[-120:] if v is not None]
            if rec.get("v24h") is None and rec["chart"]:
                rec["v24h"] = rec["chart"][-1][1]
            ERR[pid] = "summary ok"
        except Exception as e:
            ERR[pid] = f"summary {type(e).__name__}: {e}"
        out["projects"][pid] = rec
    out["fetch"] = ERR
    json.dump(out, open(OUT, "w"), indent=1)


if __name__ == "__main__":
    sys.exit(main())

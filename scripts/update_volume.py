#!/usr/bin/env python3
"""Hourly perp stats -> data/volume.json (stdlib only).

24h volume + open interest + pairs: CoinGecko derivatives exchanges (free).
Open-interest history: DefiLlama open-interest summaries (free).
Volume history is built here, one point per run.
"""
import json, os, sys, time, urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "volume.json")
UA = {"User-Agent": "Mozilla/5.0 perp-maxing", "Accept": "application/json"}

# project id -> (CoinGecko derivatives exchange id, DefiLlama slug)
SRC = {
    "variational": ("variational-omni", "variational"),
    "lighter": ("robinhood-chain-lighter-futures", "lighter-robinhood-perps"),
    "extended": ("extended", "extended-perps"),
    "risex": ("risex", "risex"),
    "nado": ("nado", "nado-perps"),
    "entropy": (None, "entropy.io"),
    "arcus": ("arcus-futures", "arcus-perps"),
}


def get(url):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.loads(r.read())
        except Exception:
            if attempt == 2:
                raise
            time.sleep(5)


def main():
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H:00Z")
    try:
        old = json.load(open(OUT))
    except Exception:
        old = {}
    out = {"updated": now.strftime("%Y-%m-%dT%H:%MZ"), "sources": ["CoinGecko", "DefiLlama"], "projects": {}, "status": {}}

    btc = None
    try:
        btc = get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")["bitcoin"]["usd"]
    except Exception as e:
        out["status"]["btc"] = str(e)
    cg = {}
    try:
        for page in (1, 2):
            for r in get(f"https://api.coingecko.com/api/v3/derivatives/exchanges?per_page=100&page={page}"):
                cg[r["id"]] = r
        out["status"]["coingecko"] = f"{len(cg)} exchanges"
    except Exception as e:
        out["status"]["coingecko"] = str(e)
    dl = {}
    try:
        d = get("https://api.llama.fi/overview/open-interest?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true")
        dl = {p["slug"]: p for p in d.get("protocols", [])}
        out["status"]["defillama"] = f"{len(dl)} protocols"
    except Exception as e:
        out["status"]["defillama"] = str(e)

    for pid, (cg_id, slug) in SRC.items():
        prev = (old.get("projects") or {}).get(pid, {})
        rec = {"vhist": prev.get("vhist", []), "oi_chart": prev.get("oi_chart", [])}
        c = cg.get(cg_id) if cg_id else None
        if c and btc:
            rec["v24h"] = round(float(c.get("trade_volume_24h_btc") or 0) * btc)
            rec["oi_cg"] = round(float(c.get("open_interest_btc") or 0) * btc)
            rec["pairs"] = c.get("number_of_perpetual_pairs")
            rec["cg_url"] = c.get("url")
        p = dl.get(slug)
        if p:
            rec.update({"oi": p.get("total24h"), "oi_ch1d": p.get("change_1d"), "oi_ch7d": p.get("change_7d"),
                        "oi_ch1m": p.get("change_1m"), "dl_url": f"https://defillama.com/protocol/{slug}"})
            try:
                s = get(f"https://api.llama.fi/summary/open-interest/{slug}")
                ch = s.get("totalDataChart") or []
                rec["oi_chart"] = [[int(t), round(float(v))] for t, v in ch[-180:] if v is not None]
            except Exception as e:
                out["status"][pid] = f"oi chart: {e}"
        if rec.get("v24h") is None and prev.get("v24h") is not None:
            rec["v24h"] = prev["v24h"]          # keep last known value on a failed run
        if rec.get("v24h"):
            h = rec["vhist"]
            if h and h[-1][0] == stamp:
                h[-1][1] = rec["v24h"]
            else:
                h.append([stamp, rec["v24h"]])
            del h[:-24 * 120]
        out["projects"][pid] = rec
        print(pid, rec.get("v24h"), rec.get("oi"))
    json.dump(out, open(OUT, "w"), indent=1)


if __name__ == "__main__":
    sys.exit(main())

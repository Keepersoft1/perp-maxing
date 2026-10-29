#!/usr/bin/env python3
"""One-off: daily volume history per perp -> data/vol_history.json (tries several free sources)."""
import json, os, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "Mozilla/5.0 perp-maxing", "Accept": "application/json"}
SLUGS = {
 "variational": ["variational", "variational-omni"],
 "lighter": ["lighter", "lighter-perps"],
 "lighter_rh": ["lighter-robinhood-perps"],
 "extended": ["extended", "extended-perps"],
 "risex": ["risex"],
 "nado": ["nado", "nado-perps"],
 "arcus": ["arcus", "arcus-perps"],
 "entropy": ["entropy.io", "entropy", "entropyio"],
}
URLS = [
 "https://api.llama.fi/summary/derivatives/{s}?excludeTotalDataChartBreakdown=true",
 "https://api.llama.fi/summary/dexs/{s}?excludeTotalDataChartBreakdown=true&dataType=dailyVolume",
 "https://api.llama.fi/summary/derivatives/{s}?excludeTotalDataChartBreakdown=true&dataType=dailyVolume",
]
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return str(e), None
out, log = {}, {}
for pid, slugs in SLUGS.items():
    for s in slugs:
        for t in URLS:
            u = t.format(s=s); code, d = get(u); log[u] = code
            ch = (d or {}).get("totalDataChart") or []
            if ch:
                out[pid] = {"slug": s, "src": u, "chart": [[int(a), round(float(b))] for a, b in ch if b is not None]}
                break
            time.sleep(1)
        if pid in out: break
json.dump({"projects": out, "log": log}, open(os.path.join(ROOT, "data", "vol_history.json"), "w"))
print(json.dumps(log, indent=1)); print({k: len(v["chart"]) for k, v in out.items()})

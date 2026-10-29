#!/usr/bin/env python3
"""One-off: daily volume history per perp -> data/vol_history.json (CoinGecko exchange volume_chart, BTC -> USD)."""
import json, os, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "Mozilla/5.0 perp-maxing", "Accept": "application/json"}
CG = {"variational": ["variational-omni", "variational"], "lighter_rh": ["robinhood-chain-lighter-futures"],
      "lighter": ["lighter", "lighter-futures"], "extended": ["extended"], "risex": ["risex"], "nado": ["nado"],
      "arcus": ["arcus-futures", "arcus"], "entropy": ["entropy", "entropy-io"]}
def get(u):
    for a in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
                return 200, json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(40); continue
            return e.code, None
        except Exception as e:
            return str(e), None
    return 429, None
log, out = {}, {}
c, btc = get("https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=365&interval=daily")
bp = {int(t // 86400000): p for t, p in (btc or {}).get("prices", [])}
log["btc"] = c
for pid, ids in CG.items():
    for i in ids:
        time.sleep(15)
        u = f"https://api.coingecko.com/api/v3/exchanges/{i}/volume_chart?days=365"
        c, d = get(u); log[u] = c
        if d:
            try:
                pts = []
                for t, v in d:
                    day = int(float(t) // 86400000); p = bp.get(day) or bp.get(day - 1)
                    if p: pts.append([day * 86400, round(float(v) * p)])
                out[pid] = {"cg": i, "chart": pts}; break
            except Exception as e:
                log[u] = f"parse: {e} {str(d)[:200]}"
log["btc_days"] = len(bp)
json.dump({"projects": out, "log": log}, open(os.path.join(ROOT, "data", "vol_history.json"), "w"))
print(json.dumps(log, indent=1)); print({k: len(v["chart"]) for k, v in out.items()})

#!/usr/bin/env python3
"""One-off: peers FDV / 30d volume -> data/var_peers.json"""
import json, os, time, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "Mozilla/5.0 perp-maxing", "Accept": "application/json"}
def get(u):
    for a in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(40); continue
            return {"err": e.code}
        except Exception as e:
            return {"err": str(e)}
    return {"err": 429}
PEERS = {"Hyperliquid": "hyperliquid", "Lighter": "lighter", "Aster": "aster", "edgeX": "edgex", "Grvt": "grvt", "ApeX": "apex", "GMX": "gmx", "Paradex": "paradex", "dYdX": "dydx", "Drift": "drift"}
log = {}
ex = []
for page in (1, 2, 3):
    r = get(f"https://api.coingecko.com/api/v3/derivatives/exchanges?per_page=100&page={page}")
    if isinstance(r, list): ex += r
    time.sleep(8)
log["exchanges"] = [[e["id"], e["name"]] for e in ex]
btc = get("https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=31&interval=daily")
bp = {int(t // 86400000): p for t, p in btc.get("prices", [])} if isinstance(btc, dict) else {}
out = {}
for nm, q in PEERS.items():
    rec = {}
    s = get("https://api.coingecko.com/api/v3/search?query=" + urllib.parse.quote(q)); time.sleep(6)
    coins = (s.get("coins") or [])[:5] if isinstance(s, dict) else []
    rec["coin_candidates"] = [[c["id"], c["symbol"], c.get("market_cap_rank")] for c in coins]
    cands = [e for e in ex if q in e["id"].lower() or q in e["name"].lower()]
    rec["ex_candidates"] = [[e["id"], e["name"], e.get("trade_volume_24h_btc")] for e in cands]
    out[nm] = rec
ids = ",".join(c[0] for r in out.values() for c in r["coin_candidates"][:3])
m = get("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=" + ids); time.sleep(6)
mk = {c["id"]: {"fdv": c.get("fully_diluted_valuation"), "mcap": c.get("market_cap"), "price": c.get("current_price"), "sym": c.get("symbol")} for c in m} if isinstance(m, list) else {"err": m}
for nm, rec in out.items():
    rec["markets"] = {c[0]: mk.get(c[0]) for c in rec["coin_candidates"][:3]}
    vols = {}
    for e in rec["ex_candidates"][:4]:
        d = get(f"https://api.coingecko.com/api/v3/exchanges/{e[0]}/volume_chart?days=30"); time.sleep(14)
        if isinstance(d, list):
            tot = 0
            for t, v in d:
                p = bp.get(int(float(t) // 86400000)) or bp.get(int(float(t) // 86400000) - 1)
                if p and v is not None: tot += float(v) * p
            vols[e[0]] = {"usd30d": round(tot), "n": len(d)}
        else:
            vols[e[0]] = d
    rec["vol30"] = vols
d = get("https://api.coingecko.com/api/v3/exchanges/variational-omni/volume_chart?days=30")
tot = 0
if isinstance(d, list):
    for t, v in d:
        p = bp.get(int(float(t) // 86400000)) or bp.get(int(float(t) // 86400000) - 1)
        if p and v is not None: tot += float(v) * p
json.dump({"variational_30d": round(tot), "peers": out, "log": log}, open(os.path.join(ROOT, "data", "var_peers.json"), "w"), indent=1)
print(round(tot))

#!/usr/bin/env python3
"""One-off: Entropy (Hyperliquid HIP-3 dex 'io') daily notional volume from 1d candles -> data/entropy_history.json"""
import json, os, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "https://api.hyperliquid.xyz/info"
def post(body):
    for a in range(4):
        try:
            r = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(r, timeout=60) as x:
                return json.loads(x.read())
        except Exception as e:
            err = str(e); time.sleep(5)
    return {"error": err}
log = {}
meta = post({"type": "metaAndAssetCtxs", "dex": "io"})
names = []
try:
    names = [u["name"] for u in meta[0]["universe"]]
    log["now_dayNtlVlm"] = sum(float(c.get("dayNtlVlm") or 0) for c in meta[1])
except Exception as e:
    log["meta"] = str(meta)[:300]
log["markets"] = names
start = 1767225600000  # 2026-01-01
days = {}
for n in names:
    c = post({"type": "candleSnapshot", "req": {"coin": n, "interval": "1d", "startTime": start, "endTime": int(time.time() * 1000)}})
    if isinstance(c, list):
        for k in c:
            d = int(k["t"]) // 1000
            days[d] = days.get(d, 0) + float(k["v"]) * float(k["c"])
    else:
        log[n] = str(c)[:200]
    time.sleep(0.3)
chart = [[d, round(v)] for d, v in sorted(days.items())]
json.dump({"chart": chart, "log": log}, open(os.path.join(ROOT, "data", "entropy_history.json"), "w"))
print(log, len(chart), chart[-3:])

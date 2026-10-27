#!/usr/bin/env python3
"""Cross-venue perp snapshot for the Arbitrage tab -> data/arb.json (stdlib only).

Source: CoinGecko derivatives exchange tickers (price, funding, OI, volume per pair).
"""
import json, os, re, sys, time, urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "arb.json")
UA = {"User-Agent": "Mozilla/5.0 perp-maxing", "Accept": "application/json"}

VENUES = {  # our project id -> CoinGecko derivatives exchange id
    "variational": "variational-omni",
    "lighter": "robinhood-chain-lighter-futures",
    "extended": "extended",
    "risex": "risex",
    "nado": "nado",
    "arcus": "arcus-futures",
}


def get(url):
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.loads(r.read())
        except Exception as e:
            if attempt == 4:
                raise
            time.sleep(35 if "429" in str(e) else 8)


def norm_base(t):
    b = (t.get("base") or t.get("symbol") or "").upper()
    b = re.sub(r"[-_/ ].*$", "", b)
    b = re.sub(r"(USDT|USDC|USD|PERP)$", "", b) or b
    b = re.sub(r"^(1000000|1000|1M|K)(?=[A-Z])", "", b)
    return b


def f(x):
    try:
        return float(x)
    except Exception:
        return None


def main():
    now = datetime.now(timezone.utc)
    out = {"updated": now.strftime("%Y-%m-%dT%H:%MZ"), "source": "CoinGecko", "venues": {}, "assets": {}, "status": {}}
    time.sleep(20)  # the volume step just used the same API
    for pid, cg in VENUES.items():
        try:
            d = get(f"https://api.coingecko.com/api/v3/derivatives/exchanges/{cg}?include_tickers=unexpired")
        except Exception as e:
            out["status"][pid] = str(e)
            continue
        tick = d.get("tickers") or []
        out["venues"][pid] = {"name": d.get("name"), "pairs": len(tick), "url": d.get("url")}
        if tick and "sample" not in out:
            out["sample"] = {k: v for k, v in tick[0].items() if not isinstance(v, (dict, list))}
        for t in tick:
            if (t.get("contract_type") or "perpetual") != "perpetual":
                continue
            base = norm_base(t)
            price = f(t.get("last")) or f((t.get("converted_last") or {}).get("usd"))
            if not base or not price:
                continue
            a = out["assets"].setdefault(base, {})
            a[pid] = {
                "sym": t.get("symbol"), "price": price,
                "fund": f(t.get("funding_rate")), "oi": f(t.get("open_interest_usd")),
                "vol": f((t.get("converted_volume") or {}).get("usd")) or f(t.get("h24_volume")),
                "spread": f(t.get("bid_ask_spread")),
            }
        out["status"][pid] = f"{len(tick)} tickers"
        time.sleep(14)  # free CoinGecko API allows only a few calls per minute
    out["assets"] = {k: v for k, v in out["assets"].items() if len(v) >= 2}
    out["status"]["shared_assets"] = len(out["assets"])
    json.dump(out, open(OUT, "w"), indent=1)
    print(out["status"])


if __name__ == "__main__":
    sys.exit(main())

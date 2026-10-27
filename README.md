# perp maxing

Live OTC point prices for perp DEXs.

- `index.html` — the site (static, Vercel-ready)
- `data/prices.json` — prices + history, updated hourly
- `scripts/update_prices.py` — reads t.me/s/PointsOTC and updates prices/logos
- `.github/workflows/update-prices.yml` — runs the updater every hour

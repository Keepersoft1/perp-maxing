#!/usr/bin/env python3
"""Hourly OTC point-price updater for perp maxing.

Reads the public preview of Telegram OTC channels (t.me/s/<channel>),
finds the latest price mention for every tracked perp, and writes
data/prices.json. Also downloads missing project logos into logos/.
Standard library only, so it runs on a bare GitHub Actions runner.
"""
import html, json, os, re, sys, time, urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "prices.json")
LOGOS = os.path.join(ROOT, "logos")
CHANNELS = ["PointsOTC"]          # public channels only (t.me/s/<name>)
MAX_AGE_H = 96                    # ignore mentions older than this
UA = {"User-Agent": "Mozilla/5.0 (perp-maxing price bot)"}

# project id -> words that identify it in an OTC message
ALIASES = {
    "variational": ["variational", "omni", "var points", "$var", "vari"],
    "lighter": ["lighter", "lit points", "lighter points"],
    "extended": ["extended", "x10"],
    "risex": ["risex", "rise x", "rise points", "rise chain"],
    "aster": ["aster"],
}
LOGO_SRC = {
    "variational": "variational.io",
    "lighter": "lighter.xyz",
    "extended": "extended.exchange",
    "risex": "risechain.com",
    "aster": "asterdex.com",
}

NUM = r"\d{1,4}(?:[.,]\d{1,3})?"
PRICE = re.compile(
    r"(?:\$\s?(?P<a1>" + NUM + r")(?:\s?[-–/]\s?\$?\s?(?P<b1>" + NUM + r"))?)"
    r"|(?:(?P<a2>" + NUM + r")(?:\s?[-–/]\s?(?P<b2>" + NUM + r"))?\s?(?:\$|(?:usd[tc]?)\b))",
    re.I,
)


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def messages(channel):
    page = get(f"https://t.me/s/{channel}").decode("utf-8", "replace")
    out = []
    for block in re.split(r'<div class="tgme_widget_message_wrap', page)[1:]:
        post = re.search(r'data-post="([^"]+)"', block)
        when = re.search(r'<time[^>]+datetime="([^"]+)"', block)
        text = re.search(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', block, re.S)
        if not (post and when and text):
            continue
        t = re.sub(r"<br\s*/?>", "\n", text.group(1))
        t = html.unescape(re.sub(r"<[^>]+>", "", t))
        ts = datetime.fromisoformat(when.group(1).replace("Z", "+00:00"))
        out.append({"post": post.group(1), "time": ts, "text": t})
    return out


def num(s):
    return float(s.replace(",", "."))


def find_price(text, aliases):
    """Return (mid, label) for the first price written next to a project name."""
    for line in text.splitlines():
        low = line.lower()
        idx = min((low.find(a) for a in aliases if a in low), default=-1)
        if idx < 0:
            continue
        seg = line[idx: idx + 70]
        m = PRICE.search(seg)
        if not m:
            continue
        a = m.group("a1") or m.group("a2")
        b = m.group("b1") or m.group("b2")
        lo = num(a)
        hi = num(b) if b else lo
        if hi < lo:
            lo, hi = hi, lo
        if not (0.01 <= lo <= 5000) or hi > lo * 3:
            continue
        mid = round((lo + hi) / 2, 4)
        label = f"${lo:g}" if lo == hi else f"${lo:g}–{hi:g}"
        return mid, label
    return None


def fetch_logos():
    os.makedirs(LOGOS, exist_ok=True)
    for pid, dom in LOGO_SRC.items():
        path = os.path.join(LOGOS, f"{pid}.png")
        if os.path.exists(path) and os.path.getsize(path) > 500:
            continue
        try:
            img = get(f"https://www.google.com/s2/favicons?domain={dom}&sz=256")
            if len(img) > 500:
                open(path, "wb").write(img)
                print("logo", pid, len(img))
        except Exception as e:  # logo is optional; site falls back to initials
            print("logo fail", pid, e)


def main():
    data = json.load(open(DATA))
    now = datetime.now(timezone.utc)
    msgs = []
    for ch in CHANNELS:
        try:
            msgs += messages(ch)
        except Exception as e:
            print("channel fail", ch, e)
    msgs.sort(key=lambda m: m["time"], reverse=True)
    print(f"{len(msgs)} messages read")
    changed = False
    for pid, aliases in ALIASES.items():
        proj = data["projects"].setdefault(pid, {"history": []})
        for m in msgs:
            if (now - m["time"]).total_seconds() > MAX_AGE_H * 3600:
                break
            hit = find_price(m["text"], aliases)
            if not hit:
                continue
            mid, label = hit
            stamp = now.strftime("%Y-%m-%dT%H:00Z")
            proj.update({
                "price": mid, "label": label, "live": True,
                "source": f"https://t.me/{m['post']}",
                "seen": m["time"].strftime("%Y-%m-%dT%H:%MZ"),
            })
            hist = proj.setdefault("history", [])
            if hist and hist[-1][0] == stamp:
                hist[-1][1] = mid
            else:
                hist.append([stamp, mid])
            del hist[:-3000]
            changed = True
            print(pid, label, m["post"])
            break
    data["updated"] = now.strftime("%Y-%m-%dT%H:%MZ")
    json.dump(data, open(DATA, "w"), indent=1)
    fetch_logos()
    print("changed" if changed else "no new prices")


if __name__ == "__main__":
    sys.exit(main())

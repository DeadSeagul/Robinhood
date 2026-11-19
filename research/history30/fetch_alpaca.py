"""Download 5-minute SIP bars (QQQ by default) from Alpaca into a CSV (see PREREG2.md).

The Alpaca key is injected by the environment's network proxy for data.alpaca.markets; nothing here
reads or stores a key.

Usage: python3 -I research/history30/fetch_alpaca.py <out.csv> [--symbol QQQ] [--adjustment split|raw] [--start 2016-01-04] [--end 2026-11-18]
"""
import argparse
import csv
import json
import subprocess
import time
import urllib.parse

BASE = "https://data.alpaca.markets/v2/stocks/{symbol}/bars"


def get(symbol, params, tries=6):
    url = BASE.format(symbol=symbol) + "?" + urllib.parse.urlencode(params)
    for k in range(tries):
        out = subprocess.run(["curl", "-sS", "--fail-with-body", "-m", "120", url], capture_output=True, text=True)
        if not out.returncode:
            return json.loads(out.stdout)
        time.sleep(10 * (k + 1))  # rate limit or a dropped connection: wait and retry
    raise SystemExit(f"request failed ({out.returncode}): {out.stdout[:300]} {out.stderr[:300]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--start", default="2016-01-04")
    ap.add_argument("--end", default="2026-11-18")
    ap.add_argument("--symbol", default="QQQ")
    ap.add_argument("--adjustment", default="split")
    a = ap.parse_args()
    params = {"timeframe": "5Min", "start": f"{a.start}T00:00:00Z", "end": f"{a.end}T23:59:59Z",
              "limit": 10000, "adjustment": a.adjustment, "feed": "sip"}
    n, pages = 0, 0
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "o", "h", "l", "c", "v"])
        while True:
            d = get(a.symbol, params)
            for b in d.get("bars") or []:
                w.writerow([b["t"], b["o"], b["h"], b["l"], b["c"], b["v"]])
                n += 1
            pages += 1
            tok = d.get("next_page_token")
            if not tok:
                break
            params["page_token"] = tok
    print(f"wrote {n} bars in {pages} pages to {a.out}")


if __name__ == "__main__":
    main()

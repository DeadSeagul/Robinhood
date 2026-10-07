#!/usr/bin/env bash
# Download Yahoo chart JSON for the backtests: 60 days of 5-minute bars and 2 years of daily bars.
# Usage: research/fetch_data.sh <out_dir> [SYMBOL ...]   (default symbols: SPY QQQ)
set -euo pipefail
out=${1:?usage: fetch_data.sh <out_dir> [SYMBOL ...]}
shift
syms=("$@")
[ ${#syms[@]} -eq 0 ] && syms=(SPY QQQ)
mkdir -p "$out"
for s in "${syms[@]}"; do
  curl -sS -m 30 -A "Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/$s?interval=5m&range=60d" -o "$out/${s}_5m.json"
  curl -sS -m 30 -A "Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/$s?interval=1d&range=2y" -o "$out/${s}_1d.json"
done

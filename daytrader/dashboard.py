"""Self-contained HTML dashboard: stat tiles, equity vs SPY, drawdown, trade table, per variant."""
from __future__ import annotations

import json
import math
from pathlib import Path

TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ORB Backtest Dashboard</title>
<style>
.viz-root{color-scheme:light;--page:#f9f9f7;--surface-1:#fcfcfb;--text-primary:#0b0b0b;--text-secondary:#52514e;
--muted:#898781;--grid:#e1e0d9;--axis:#c3c2b7;--border:rgba(11,11,11,.10);--series-1:#2a78d6;--series-2:#eb6834;
--good:#006300;--bad:#d03b3b}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])) .viz-root{color-scheme:dark;--page:#0d0d0d;
--surface-1:#1a1a19;--text-primary:#fff;--text-secondary:#c3c2b7;--muted:#898781;--grid:#2c2c2a;--axis:#383835;
--border:rgba(255,255,255,.10);--series-1:#3987e5;--series-2:#d95926;--good:#0ca30c;--bad:#e66767}}
:root[data-theme="dark"] .viz-root{color-scheme:dark;--page:#0d0d0d;--surface-1:#1a1a19;--text-primary:#fff;
--text-secondary:#c3c2b7;--muted:#898781;--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);
--series-1:#3987e5;--series-2:#d95926;--good:#0ca30c;--bad:#e66767}
*{box-sizing:border-box}body{margin:0}
.viz-root{background:var(--page);color:var(--text-primary);font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif;
min-height:100vh;padding:24px 16px}
.wrap{max-width:1100px;margin:0 auto}h1{font-size:20px;margin:0 0 4px}h2{font-size:15px;margin:0 0 12px}
.sub{color:var(--text-secondary);margin:0 0 16px}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 16px}
.filters button{font:inherit;border:1px solid var(--border);background:var(--surface-1);color:var(--text-primary);
border-radius:8px;padding:6px 12px;cursor:pointer}.filters button[aria-pressed="true"]{font-weight:600;outline:2px solid var(--series-1)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:16px}
.tile,.card{background:var(--surface-1);border:1px solid var(--border);border-radius:12px;padding:14px}
.tile .k{color:var(--text-secondary);font-size:12px}.tile .v{font-size:22px;font-weight:600;margin-top:2px}
.verdict{margin-bottom:16px}.verdict ul{margin:6px 0 0 18px;padding:0;color:var(--text-secondary)}
.card{margin-bottom:16px;position:relative}svg{display:block;width:100%;height:auto;overflow:visible}
.legend{display:flex;gap:16px;color:var(--text-secondary);font-size:12px;margin-bottom:6px}
.legend i{display:inline-block;width:16px;height:2px;vertical-align:middle;margin-right:6px}
.tt{position:absolute;pointer-events:none;background:var(--surface-1);border:1px solid var(--border);border-radius:8px;
padding:8px 10px;font-size:12px;box-shadow:0 4px 12px rgba(0,0,0,.12);display:none;white-space:nowrap}
.tt b{font-size:13px}.tt .row{display:flex;align-items:center;gap:6px}.tt .row i{width:12px;height:2px}
.tbl{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:12px;font-variant-numeric:tabular-nums}
th,td{text-align:right;padding:6px 8px;border-bottom:1px solid var(--grid);white-space:nowrap}
th:first-child,td:first-child,th:nth-child(2),td:nth-child(2){text-align:left}th{color:var(--text-secondary);font-weight:600}
.pos{color:var(--good)}.neg{color:var(--bad)}.note{color:var(--muted);font-size:12px}
</style></head>
<body><div class="viz-root"><div class="wrap">
<h1>ORB backtest dashboard</h1>
<p class="sub" id="sub"></p>
<div class="filters" id="filters" role="group" aria-label="Strategy variant"></div>
<div class="tiles" id="tiles"></div>
<div class="card verdict" id="verdict"></div>
<div class="card"><h2>Account equity vs buy-and-hold SPY</h2>
<div class="legend"><span><i style="background:var(--series-1)"></i>Strategy</span><span><i style="background:var(--series-2)"></i>SPY buy-and-hold</span></div>
<svg id="eq" viewBox="0 0 1000 300" role="img" aria-label="Equity curve"></svg><div class="tt" id="tt-eq"></div></div>
<div class="card"><h2>Drawdown from peak</h2><svg id="dd" viewBox="0 0 1000 180" role="img" aria-label="Drawdown"></svg>
<div class="tt" id="tt-dd"></div></div>
<div class="card"><h2>Trades</h2><div class="tbl"><table id="trades"></table></div>
<p class="note">Prices include modeled spread, slippage and fees. Equity is end-of-day.</p></div>
</div></div>
<script>
const DATA = __DATA__;
const $ = id => document.getElementById(id);
const fmt$ = v => (v < 0 ? "-$" : "$") + Math.abs(v).toLocaleString(undefined, {maximumFractionDigits: 2, minimumFractionDigits: 2});
const pct = v => (v * 100).toFixed(2) + "%";
const SVGNS = "http://www.w3.org/2000/svg";
function el(tag, attrs, parent) { const e = document.createElementNS(SVGNS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; }
function text(parent, x, y, s, attrs) { const t = el("text", Object.assign({x, y, "font-size": 11, fill: "var(--muted)"}, attrs || {}), parent); t.textContent = s; return t; }
function niceTicks(lo, hi, n) { const span = hi - lo || 1; const step = Math.pow(10, Math.floor(Math.log10(span / n))); const m = [1, 2, 2.5, 5, 10].find(m => span / (m * step) <= n) * step; const out = []; for (let v = Math.ceil(lo / m) * m; v <= hi + 1e-9; v += m) out.push(v); return out; }

function lineChart(svg, tt, dates, series, opts) {
  svg.replaceChildren();
  const W = 1000, H = +svg.getAttribute("viewBox").split(" ")[3], L = 70, R = 90, T = 10, B = 26;
  const all = series.flatMap(s => s.values);
  let lo = Math.min(...all), hi = Math.max(...all); if (opts.zeroTop) hi = 0; const pad = (hi - lo) * 0.08 || 1; lo -= pad; if (!opts.zeroTop) hi += pad;
  const x = i => L + (dates.length < 2 ? 0 : i * (W - L - R) / (dates.length - 1));
  const y = v => T + (hi - v) * (H - T - B) / (hi - lo);
  for (const v of niceTicks(lo, hi, 5)) { el("line", {x1: L, x2: W - R, y1: y(v), y2: y(v), stroke: "var(--grid)", "stroke-width": 1}, svg); text(svg, L - 8, y(v) + 4, opts.fmt(v), {"text-anchor": "end"}); }
  const step = Math.max(1, Math.ceil(dates.length / 6));
  dates.forEach((d, i) => { if (i % step === 0) text(svg, x(i), H - 6, d.slice(5), {"text-anchor": "middle"}); });
  el("line", {x1: L, x2: W - R, y1: H - B, y2: H - B, stroke: "var(--axis)"}, svg);
  for (const s of series) {
    const pts = s.values.map((v, i) => `${x(i)},${y(v)}`).join(" ");
    if (opts.area) el("polygon", {points: `${x(0)},${y(0)} ${pts} ${x(s.values.length - 1)},${y(0)}`, fill: s.color, "fill-opacity": 0.18}, svg);
    el("polyline", {points: pts, fill: "none", stroke: s.color, "stroke-width": 2, "stroke-linejoin": "round"}, svg);
  }
  // end-of-line labels, nudged apart so they never collide
  const labels = series.filter(s => s.label).map(s => ({s, y: y(s.values[s.values.length - 1]) + 4})).sort((a, b) => a.y - b.y);
  for (let i = 1; i < labels.length; i++) if (labels[i].y - labels[i - 1].y < 14) labels[i].y = labels[i - 1].y + 14;
  for (const l of labels) text(svg, x(dates.length - 1) + 8, l.y, l.s.label, {fill: "var(--text-secondary)"});
  const cross = el("line", {y1: T, y2: H - B, stroke: "var(--axis)", "stroke-width": 1, visibility: "hidden"}, svg);
  const hit = el("rect", {x: L, y: T, width: W - L - R, height: H - T - B, fill: "transparent", tabindex: 0}, svg);
  function show(i, cx, cy) {
    cross.setAttribute("x1", x(i)); cross.setAttribute("x2", x(i)); cross.setAttribute("visibility", "visible");
    tt.replaceChildren(); const h = document.createElement("div"); h.textContent = dates[i]; h.style.color = "var(--text-secondary)"; tt.appendChild(h);
    for (const s of series) { const r = document.createElement("div"); r.className = "row"; const k = document.createElement("i"); k.style.background = s.color; const b = document.createElement("b"); b.textContent = opts.fmt(s.values[i]); const n = document.createElement("span"); n.textContent = s.name; n.style.color = "var(--text-secondary)"; r.append(k, b, n); tt.appendChild(r); }
    tt.style.display = "block"; tt.style.left = Math.min(cx + 14, svg.parentNode.clientWidth - tt.offsetWidth - 8) + "px"; tt.style.top = (cy + 10) + "px";
  }
  hit.addEventListener("pointermove", e => { const r = svg.getBoundingClientRect(); const px = (e.clientX - r.left) * 1000 / r.width; const i = Math.max(0, Math.min(dates.length - 1, Math.round((px - L) / ((W - L - R) / Math.max(1, dates.length - 1))))); show(i, e.clientX - svg.parentNode.getBoundingClientRect().left, e.clientY - svg.parentNode.getBoundingClientRect().top); });
  hit.addEventListener("pointerleave", () => { tt.style.display = "none"; cross.setAttribute("visibility", "hidden"); });
  hit.addEventListener("focus", () => show(dates.length - 1, 40, 20));
  hit.addEventListener("blur", () => { tt.style.display = "none"; cross.setAttribute("visibility", "hidden"); });
}

function render(name) {
  const v = DATA.variants[name], m = v.metrics;
  [...$("filters").children].forEach(b => b.setAttribute("aria-pressed", b.dataset.v === name));
  $("sub").textContent = `${DATA.period} · ${DATA.universe_size} symbols · data: ${DATA.source} · start equity ${fmt$(DATA.start_equity)}`;
  const tiles = [["Net profit after costs", fmt$(m.net_profit)], ["Trades", m.trades], ["Win rate", pct(m.win_rate)],
    ["Expectancy / trade", fmt$(m.expectancy) + ` (${m.expectancy_r.toFixed(2)}R)`], ["Profit factor", isFinite(m.profit_factor) ? m.profit_factor.toFixed(2) : "n/a"],
    ["Max drawdown", pct(m.max_drawdown_pct)], ["Sharpe (daily, ann.)", m.sharpe.toFixed(2)], ["SPY buy-and-hold", pct(DATA.spy_return)]];
  $("tiles").replaceChildren(...tiles.map(([k, val]) => { const d = document.createElement("div"); d.className = "tile"; const a = document.createElement("div"); a.className = "k"; a.textContent = k; const b = document.createElement("div"); b.className = "v"; b.textContent = val; d.append(a, b); return d; }));
  const vd = $("verdict"); vd.replaceChildren(); const h = document.createElement("h2"); h.textContent = v.pass ? "Screen: PASS" : "Screen: FAIL — do not trade this live"; vd.appendChild(h);
  const ul = document.createElement("ul"); (v.fails.length ? v.fails : ["meets the minimum screen; still not proof of future profit"]).forEach(f => { const li = document.createElement("li"); li.textContent = f; ul.appendChild(li); }); vd.appendChild(ul);
  lineChart($("eq"), $("tt-eq"), v.dates, [{name: "Strategy", label: "Strategy", values: v.equity, color: "var(--series-1)"}, {name: "SPY buy-and-hold", label: "SPY", values: v.spy, color: "var(--series-2)"}], {fmt: fmt$});
  lineChart($("dd"), $("tt-dd"), v.dates, [{name: "Drawdown", values: v.drawdown, color: "var(--series-1)"}], {fmt: pct, area: true, zeroTop: true});
  const t = $("trades"); t.replaceChildren(); const cols = ["date", "symbol", "entry", "exit", "qty", "exit reason", "net P/L", "R", "costs"];
  const hr = document.createElement("tr"); cols.forEach(c => { const th = document.createElement("th"); th.textContent = c; hr.appendChild(th); }); t.appendChild(hr);
  if (!v.trades.length) { const r = document.createElement("tr"); const td = document.createElement("td"); td.colSpan = cols.length; td.textContent = "NO TRADES"; r.appendChild(td); t.appendChild(r); }
  v.trades.forEach(tr => { const r = document.createElement("tr"); [tr.date, tr.symbol, tr.entry, tr.exit, tr.qty, tr.reason, fmt$(tr.pnl), tr.r.toFixed(2), fmt$(tr.costs)].forEach((c, i) => { const td = document.createElement("td"); td.textContent = c; if (i === 6) td.className = tr.pnl >= 0 ? "pos" : "neg"; r.appendChild(td); }); t.appendChild(r); });
}
Object.keys(DATA.variants).forEach((name, i) => { const b = document.createElement("button"); b.type = "button"; b.dataset.v = name; b.textContent = name; b.onclick = () => render(name); $("filters").appendChild(b); });
render(Object.keys(DATA.variants)[0]);
</script></body></html>
"""


def _clean(v):
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None if math.isnan(v) else 1e9
    return v


def write_dashboard(path: str | Path, payload: dict) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(payload, default=_clean).replace("</", "<\\/")
    path.write_text(TEMPLATE.replace("__DATA__", blob))
    return path

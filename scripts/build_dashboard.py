"""Build a self-contained six-panel HTML dashboard from JSONL logs."""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app.dashboard import calculate, load_records


def status(value: float, operator: str, threshold: float) -> str:
    passed = value <= threshold if operator == "lte" else value >= threshold
    return "PASS" if passed else "BREACH"


def panel(title: str, body: str, threshold: str, state: str) -> str:
    return f'<section class="panel {state.lower()}"><h2>{html.escape(title)}</h2><div class="values">{body}</div><p>Threshold: {html.escape(threshold)} · <strong>{state}</strong></p></section>'


def render(metrics: dict) -> str:
    latency = metrics["latency"]
    traffic = metrics["traffic"]
    errors = metrics["errors"]
    cost = metrics["cost"]
    tokens = metrics["tokens"]
    quality = metrics["quality"]
    items = [
        panel("Latency percentiles", f"P50 <b>{latency['p50']:.0f} ms</b><br>P95 <b>{latency['p95']:.0f} ms</b><br>P99 <b>{latency['p99']:.0f} ms</b>", "P95 ≤ 3000 ms", status(latency["p95"], "lte", 3000)),
        panel("Request traffic", f"Total <b>{traffic['count']}</b><br>Peak <b>{traffic['peak_per_minute']} req/min</b><br><small>{html.escape(json.dumps(traffic['by_minute']))}</small>", "≥ 1 req/min", status(traffic["peak_per_minute"], "gte", 1)),
        panel("Error rate and breakdown", f"Error rate <b>{errors['error_rate_pct']:.2f}%</b><br>Failed <b>{errors['failed_requests']}</b><br><small>{html.escape(json.dumps(errors['breakdown']))}</small>", "≤ 2%", status(errors["error_rate_pct"], "lte", 2)),
        panel("Cost over time", f"Total <b>${cost['total']:.4f}</b><br><small>{html.escape(json.dumps(cost['by_minute']))}</small>", "≤ $2.50", status(cost["total"], "lte", 2.5)),
        panel("Input and output tokens", f"Input <b>{tokens['input']}</b><br>Output <b>{tokens['output']}</b>", "≤ 50000 tokens", status(tokens["input"] + tokens["output"], "lte", 50000)),
        panel("Quality proxy", f"Mean score <b>{quality['mean']:.2f}</b>", "≥ 0.75", status(quality["mean"], "gte", 0.75)),
    ]
    return """<!doctype html><html><head><meta charset=\"utf-8\"><meta http-equiv=\"refresh\" content=\"30\"><title>Day 13 AI Observability</title><style>body{font-family:Arial,sans-serif;background:#101826;color:#e8eefb;margin:0;padding:28px}header{display:flex;justify-content:space-between;align-items:end;border-bottom:1px solid #334155;margin-bottom:20px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.panel{background:#172235;border-radius:12px;padding:16px;min-height:150px;border-left:6px solid #22c55e}.panel.breach{border-left-color:#ef4444}.panel h2{margin:0 0 14px;font-size:18px}.values{line-height:1.7;font-size:16px}small{color:#b7c5db;word-break:break-word}p{color:#b7c5db;font-size:13px}@media(max-width:800px){.grid{grid-template-columns:1fr}}</style></head><body><header><div><h1>Day 13 AI Observability</h1><p>Source: data/logs.jsonl · Range: last 60 minutes · Refresh: 30 seconds</p></div></header><main class=\"grid\">""" + "".join(items) + "</main></body></html>"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=REPO_ROOT / "data" / "logs.jsonl")
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "dashboard.html")
    args = parser.parse_args()
    args.output.write_text(render(calculate(load_records(args.input))), encoding="utf-8")
    print(f"Dashboard written: {args.output}")


if __name__ == "__main__":
    main()

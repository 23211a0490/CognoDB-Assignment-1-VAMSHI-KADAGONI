#!/usr/bin/env python3
"""
Reads the most recent results/run_*.json and prints markdown tables in the
same shape as the templates in README.md section 6, ready to paste in.

Usage: python results/render_tables.py [path/to/run_XXXX.json]
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

DISPLAY_NAMES = {
    "cognodb": "CognoDB",
    "neo4j_aura": "Neo4j AuraDB Free",
    "memgraph": "Memgraph Cloud",
    "arangodb": "ArangoDB Oasis",
    "janusgraph": "JanusGraph (capped)",
}


def latest_results_path():
    files = sorted(glob.glob(os.path.join(HERE, "run_*.json")))
    if not files:
        raise SystemExit("No results/run_*.json files found. Run run_benchmark.py first.")
    return files[-1]


def fmt(v, suffix=""):
    return f"{v}{suffix}" if v is not None else "N/A"


def render(results):
    by_platform = {r["platform"]: r for r in results}
    order = [p for p in DISPLAY_NAMES if p in by_platform]

    out = []

    out.append("### Data loading\n")
    out.append("| Platform | Nodes/sec | Rels/sec | Total load time |")
    out.append("|---|---|---|---|")
    for p in order:
        r = by_platform[p]
        if r["status"] != "ok":
            out.append(f"| {DISPLAY_NAMES[p]} | FAILED: {r.get('error')} | | |")
            continue
        l = r["load"]
        out.append(f"| {DISPLAY_NAMES[p]} | {l['nodes_per_sec']} | {l['rels_per_sec']} | {l['total_seconds']}s |")

    out.append("\n### Traversals (p50 / p95, ms)\n")
    out.append("| Platform | 1-hop | 2-hop | 3-hop |")
    out.append("|---|---|---|---|")
    for p in order:
        r = by_platform[p]
        if r["status"] != "ok":
            continue
        t = r["traversals"]
        row = " | ".join(
            f"{fmt(t[h]['p50'])} / {fmt(t[h]['p95'])}" for h in ("1_hop", "2_hop", "3_hop")
        )
        out.append(f"| {DISPLAY_NAMES[p]} | {row} |")

    out.append("\n### Lookups (p50 / p95, ms)\n")
    out.append("| Platform | Point lookup | Indexed/filtered lookup | Indexed properties |")
    out.append("|---|---|---|---|")
    for p in order:
        r = by_platform[p]
        if r["status"] != "ok":
            continue
        lk = r["lookups"]
        pt = lk["point_lookup"]
        fl = lk["filtered_lookup"]
        idx = ", ".join(r.get("indexed_properties", []))
        out.append(
            f"| {DISPLAY_NAMES[p]} | {fmt(pt['p50'])} / {fmt(pt['p95'])} | "
            f"{fmt(fl['p50'])} / {fmt(fl['p95'])} | {idx} |"
        )

    out.append("\n### Aggregations (p50 / p95, ms)\n")
    out.append("| Platform | Count by relationship type |")
    out.append("|---|---|")
    for p in order:
        r = by_platform[p]
        if r["status"] != "ok":
            continue
        a = r["aggregations"]["count_by_rel_type"]
        out.append(f"| {DISPLAY_NAMES[p]} | {fmt(a['p50'])} / {fmt(a['p95'])} |")

    out.append("\n### Mixed workload throughput (queries/sec)\n")
    levels = set()
    for r in by_platform.values():
        if r["status"] == "ok":
            levels.update(r["mixed"].keys())
    levels = sorted(levels, key=lambda s: int(s.split("_")[0]))
    header = "| Platform | " + " | ".join(l.replace("_", " ") for l in levels) + " |"
    out.append(header)
    out.append("|" + "---|" * (len(levels) + 1))
    for p in order:
        r = by_platform[p]
        if r["status"] != "ok":
            continue
        row = " | ".join(str(r["mixed"].get(l, {}).get("qps", "N/A")) for l in levels)
        out.append(f"| {DISPLAY_NAMES[p]} | {row} |")

    out.append("\n### Footprint\n")
    out.append("| Platform | Stored data size | Memory usage |")
    out.append("|---|---|---|")
    for p in order:
        r = by_platform[p]
        if r["status"] != "ok":
            continue
        fp = r.get("footprint", {})
        out.append(f"| {DISPLAY_NAMES[p]} | {fp.get('stored_data_size', 'N/A')} | {fp.get('memory_usage', 'N/A')} |")

    return "\n".join(out)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else latest_results_path()
    with open(path) as f:
        results = json.load(f)
    md = render(results)
    print(md)
    out_path = os.path.join(HERE, "summary_tables.md")
    with open(out_path, "w") as f:
        f.write(md + "\n")
    print(f"\n(also written to {out_path})", file=sys.stderr)


if __name__ == "__main__":
    main()

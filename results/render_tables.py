#!/usr/bin/env python3

"""
Generate benchmark summary tables and comparison graphs
from results/summary.json.

Platforms:
- CognoDB
- Neo4j AuraDB
- Memgraph Cloud
- ArangoDB Oasis
- FalkorDB Cloud

Usage:
    python results/render_tables.py
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent.parent
SUMMARY_FILE = ROOT / "results" / "summary.json"
OUTPUT_MD = ROOT / "results" / "summary_tables.md"
GRAPH_DIR = ROOT / "results" / "graphs"

GRAPH_DIR.mkdir(parents=True, exist_ok=True)


DISPLAY_NAMES = [
    "CognoDB",
    "Neo4j AuraDB",
    "Memgraph Cloud",
    "ArangoDB Oasis",
    "FalkorDB Cloud",
]


def load_summary():
    if not SUMMARY_FILE.exists():
        raise FileNotFoundError(
            f"Could not find {SUMMARY_FILE}"
        )

    with open(SUMMARY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_run(data, platform):
    runs = data.get(platform, [])

    if not runs:
        return None

    return runs[-1]


def fmt(value):
    if value is None:
        return "N/A"

    if isinstance(value, float):
        return f"{value:.2f}"

    return str(value)


def make_tables(data):

    runs = {
        platform: get_run(data, platform)
        for platform in DISPLAY_NAMES
    }

    out = []

    # ---------------------------------------------------------
    # Data loading
    # ---------------------------------------------------------

    out.append("### Data loading\n")
    out.append(
        "| Platform | Nodes/sec | Rels/sec | Total load time |"
    )
    out.append("|---|---:|---:|---:|")

    for platform in DISPLAY_NAMES:

        r = runs[platform]

        if not r:
            out.append(f"| {platform} | N/A | N/A | N/A |")
            continue

        load = r["load"]

        out.append(
            f"| {platform} | "
            f"{fmt(load.get('nodes_per_sec'))} | "
            f"{fmt(load.get('rels_per_sec'))} | "
            f"{fmt(load.get('total_seconds'))} s |"
        )

    # ---------------------------------------------------------
    # Traversals
    # ---------------------------------------------------------

    out.append("\n### Traversals (p50 / p95, ms)\n")
    out.append("| Platform | 1-hop | 2-hop | 3-hop |")
    out.append("|---|---:|---:|---:|")

    for platform in DISPLAY_NAMES:

        r = runs[platform]

        if not r:
            continue

        t = r["traversals"]

        out.append(
            f"| {platform} | "
            f"{fmt(t['1_hop']['p50'])} / {fmt(t['1_hop']['p95'])} | "
            f"{fmt(t['2_hop']['p50'])} / {fmt(t['2_hop']['p95'])} | "
            f"{fmt(t['3_hop']['p50'])} / {fmt(t['3_hop']['p95'])} |"
        )

    # ---------------------------------------------------------
    # Lookups
    # ---------------------------------------------------------

    out.append("\n### Lookups (p50 / p95, ms)\n")
    out.append(
        "| Platform | Point lookup | Indexed/filtered lookup | Indexed properties |"
    )
    out.append("|---|---:|---:|---|")

    for platform in DISPLAY_NAMES:

        r = runs[platform]

        if not r:
            continue

        lookups = r["lookups"]

        point = lookups["point_lookup"]
        filtered = lookups["filtered_lookup"]

        indexed = ", ".join(
            r.get("indexed_properties", [])
        )

        out.append(
            f"| {platform} | "
            f"{fmt(point['p50'])} / {fmt(point['p95'])} | "
            f"{fmt(filtered['p50'])} / {fmt(filtered['p95'])} | "
            f"{indexed} |"
        )

    # ---------------------------------------------------------
    # Aggregations
    # ---------------------------------------------------------

    out.append("\n### Aggregations (p50 / p95, ms)\n")
    out.append(
        "| Platform | Count by relationship type |"
    )
    out.append("|---|---:|")

    for platform in DISPLAY_NAMES:

        r = runs[platform]

        if not r:
            continue

        aggregation = r["aggregations"]["count_by_rel_type"]

        out.append(
            f"| {platform} | "
            f"{fmt(aggregation['p50'])} / "
            f"{fmt(aggregation['p95'])} |"
        )

    # ---------------------------------------------------------
    # Mixed workload
    # ---------------------------------------------------------

    out.append(
        "\n### Mixed workload throughput (queries/sec)\n"
    )

    out.append(
        "| Platform | 1 client | 10 clients | 40 clients |"
    )
    out.append("|---|---:|---:|---:|")

    for platform in DISPLAY_NAMES:

        r = runs[platform]

        if not r:
            continue

        mixed = r["mixed"]

        out.append(
            f"| {platform} | "
            f"{fmt(mixed['1_clients']['qps'])} | "
            f"{fmt(mixed['10_clients']['qps'])} | "
            f"{fmt(mixed['40_clients']['qps'])} |"
        )

    # ---------------------------------------------------------
    # Footprint
    # ---------------------------------------------------------

    out.append("\n### Footprint\n")
    out.append(
        "| Platform | Stored data size | Memory usage |"
    )
    out.append("|---|---|---|")

    for platform in DISPLAY_NAMES:

        r = runs[platform]

        if not r:
            continue

        footprint = r.get("footprint", {})

        out.append(
            f"| {platform} | "
            f"{footprint.get('stored_data_size', 'N/A')} | "
            f"{footprint.get('memory_usage', 'N/A')} |"
        )

    return "\n".join(out)


# =============================================================
# GRAPH GENERATION
# =============================================================

def save_bar_chart(
    platforms,
    values,
    title,
    ylabel,
    filename,
):

    plt.figure(figsize=(10, 6))

    plt.bar(platforms, values)

    plt.title(title)
    plt.ylabel(ylabel)

    plt.xticks(
        rotation=20,
        ha="right"
    )

    plt.tight_layout()

    plt.savefig(
        GRAPH_DIR / filename,
        dpi=200
    )

    plt.close()


def generate_graphs(data):

    runs = {
        platform: get_run(data, platform)
        for platform in DISPLAY_NAMES
    }

    # ---------------------------------------------------------
    # Load time
    # ---------------------------------------------------------

    platforms = []
    load_times = []

    for platform in DISPLAY_NAMES:

        r = runs[platform]

        if r:
            platforms.append(platform)
            load_times.append(
                r["load"]["total_seconds"]
            )

    save_bar_chart(
        platforms,
        load_times,
        "Graph Database Load Time",
        "Seconds",
        "load_time.png",
    )

    # ---------------------------------------------------------
    # Nodes per second
    # ---------------------------------------------------------

    node_rates = [
        runs[p]["load"]["nodes_per_sec"]
        for p in platforms
    ]

    save_bar_chart(
        platforms,
        node_rates,
        "Node Ingestion Rate",
        "Nodes / second",
        "nodes_per_sec.png",
    )

    # ---------------------------------------------------------
    # Relationships per second
    # ---------------------------------------------------------

    rel_rates = [
        runs[p]["load"]["rels_per_sec"]
        for p in platforms
    ]

    save_bar_chart(
        platforms,
        rel_rates,
        "Relationship Ingestion Rate",
        "Relationships / second",
        "rels_per_sec.png",
    )

    # ---------------------------------------------------------
    # Traversal p50
    # ---------------------------------------------------------

    for hop in ["1_hop", "2_hop", "3_hop"]:

        values = [
            runs[p]["traversals"][hop]["p50"]
            for p in platforms
        ]

        hop_name = hop.replace("_", "-")

        save_bar_chart(
            platforms,
            values,
            f"{hop_name} Traversal Latency (p50)",
            "Latency (ms)",
            f"_tmp_{hop}.png",
        )

    # Combined traversal p50 graph

    plt.figure(figsize=(11, 6))

    x = range(len(platforms))

    width = 0.25

    values_1 = [
        runs[p]["traversals"]["1_hop"]["p50"]
        for p in platforms
    ]

    values_2 = [
        runs[p]["traversals"]["2_hop"]["p50"]
        for p in platforms
    ]

    values_3 = [
        runs[p]["traversals"]["3_hop"]["p50"]
        for p in platforms
    ]

    plt.bar(
        [i - width for i in x],
        values_1,
        width=width,
        label="1-hop",
    )

    plt.bar(
        x,
        values_2,
        width=width,
        label="2-hop",
    )

    plt.bar(
        [i + width for i in x],
        values_3,
        width=width,
        label="3-hop",
    )

    plt.title("Traversal Latency Comparison (p50)")
    plt.ylabel("Latency (ms)")
    plt.xticks(
        list(x),
        platforms,
        rotation=20,
        ha="right",
    )

    plt.legend()
    plt.tight_layout()

    plt.savefig(
        GRAPH_DIR / "traversal_p50.png",
        dpi=200,
    )

    plt.close()

    # ---------------------------------------------------------
    # Traversal p95
    # ---------------------------------------------------------

    plt.figure(figsize=(11, 6))

    values_1 = [
        runs[p]["traversals"]["1_hop"]["p95"]
        for p in platforms
    ]

    values_2 = [
        runs[p]["traversals"]["2_hop"]["p95"]
        for p in platforms
    ]

    values_3 = [
        runs[p]["traversals"]["3_hop"]["p95"]
        for p in platforms
    ]

    plt.bar(
        [i - width for i in x],
        values_1,
        width=width,
        label="1-hop",
    )

    plt.bar(
        x,
        values_2,
        width=width,
        label="2-hop",
    )

    plt.bar(
        [i + width for i in x],
        values_3,
        width=width,
        label="3-hop",
    )

    plt.title("Traversal Latency Comparison (p95)")
    plt.ylabel("Latency (ms)")
    plt.xticks(
        list(x),
        platforms,
        rotation=20,
        ha="right",
    )

    plt.legend()
    plt.tight_layout()

    plt.savefig(
        GRAPH_DIR / "traversal_p95.png",
        dpi=200,
    )

    plt.close()

    # ---------------------------------------------------------
    # Lookup + aggregation
    # ---------------------------------------------------------

    plt.figure(figsize=(11, 6))

    lookup = [
        runs[p]["lookups"]["point_lookup"]["p50"]
        for p in platforms
    ]

    filtered = [
        runs[p]["lookups"]["filtered_lookup"]["p50"]
        for p in platforms
    ]

    aggregation = [
        runs[p]["aggregations"]["count_by_rel_type"]["p50"]
        for p in platforms
    ]

    x = range(len(platforms))

    width = 0.25

    plt.bar(
        [i - width for i in x],
        lookup,
        width=width,
        label="Point lookup",
    )

    plt.bar(
        x,
        filtered,
        width=width,
        label="Filtered lookup",
    )

    plt.bar(
        [i + width for i in x],
        aggregation,
        width=width,
        label="Aggregation",
    )

    plt.title("Lookup and Aggregation Latency (p50)")
    plt.ylabel("Latency (ms)")
    plt.xticks(
        list(x),
        platforms,
        rotation=20,
        ha="right",
    )

    plt.legend()
    plt.tight_layout()

    plt.savefig(
        GRAPH_DIR / "lookup_aggregation.png",
        dpi=200,
    )

    plt.close()

    # ---------------------------------------------------------
    # Mixed workload QPS
    # ---------------------------------------------------------

    plt.figure(figsize=(11, 6))

    qps_1 = [
        runs[p]["mixed"]["1_clients"]["qps"]
        for p in platforms
    ]

    qps_10 = [
        runs[p]["mixed"]["10_clients"]["qps"]
        for p in platforms
    ]

    qps_40 = [
        runs[p]["mixed"]["40_clients"]["qps"]
        for p in platforms
    ]

    x = range(len(platforms))

    plt.bar(
        [i - width for i in x],
        qps_1,
        width=width,
        label="1 client",
    )

    plt.bar(
        x,
        qps_10,
        width=width,
        label="10 clients",
    )

    plt.bar(
        [i + width for i in x],
        qps_40,
        width=width,
        label="40 clients",
    )

    plt.title("Mixed Workload Throughput")
    plt.ylabel("Queries / second")
    plt.xticks(
        list(x),
        platforms,
        rotation=20,
        ha="right",
    )

    plt.legend()
    plt.tight_layout()

    plt.savefig(
        GRAPH_DIR / "mixed_qps.png",
        dpi=200,
    )

    plt.close()

    # Remove temporary individual traversal graphs
    for tmp in GRAPH_DIR.glob("_tmp_*.png"):
        tmp.unlink()

    print("Graphs generated successfully.")


def main():

    print(f"Reading: {SUMMARY_FILE}")

    data = load_summary()

    print(
        "Platforms found:"
    )

    for platform in DISPLAY_NAMES:

        if platform in data:

            print(f"  ✓ {platform}")

        else:

            print(f"  ✗ {platform}")

    # Generate markdown tables

    markdown = make_tables(data)

    with open(
        OUTPUT_MD,
        "w",
        encoding="utf-8",
    ) as f:

        f.write(markdown + "\n")

    # Generate graphs

    generate_graphs(data)

    print()
    print(
        f"Summary written to: {OUTPUT_MD}"
    )

    print(
        f"Graphs written to: {GRAPH_DIR}"
    )


if __name__ == "__main__":
    main()
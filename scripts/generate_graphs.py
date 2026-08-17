import json
from pathlib import Path

import matplotlib.pyplot as plt


RESULTS_FILE = Path("results/summary.json")
OUTPUT_DIR = Path("results/graphs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


with open(RESULTS_FILE, "r", encoding="utf-8") as f:
    results = json.load(f)


platforms = list(results.keys())


def get_result(platform):
    return results[platform][0]


# ---------------------------------------------------------
# 1. Load Time
# ---------------------------------------------------------

load_times = [
    get_result(p)["load"]["total_seconds"]
    for p in platforms
]

plt.figure(figsize=(10, 6))
plt.bar(platforms, load_times)
plt.ylabel("Load Time (seconds)")
plt.title("Graph Database Data Loading Time")
plt.xticks(rotation=20)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "load_time.png", dpi=200)
plt.close()


# ---------------------------------------------------------
# 2. Node Loading Throughput
# ---------------------------------------------------------

nodes_per_sec = [
    get_result(p)["load"]["nodes_per_sec"]
    for p in platforms
]

plt.figure(figsize=(10, 6))
plt.bar(platforms, nodes_per_sec)
plt.ylabel("Nodes per Second")
plt.title("Node Loading Throughput")
plt.xticks(rotation=20)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "nodes_per_sec.png", dpi=200)
plt.close()


# ---------------------------------------------------------
# 3. Relationship Loading Throughput
# ---------------------------------------------------------

rels_per_sec = [
    get_result(p)["load"]["rels_per_sec"]
    for p in platforms
]

plt.figure(figsize=(10, 6))
plt.bar(platforms, rels_per_sec)
plt.ylabel("Relationships per Second")
plt.title("Relationship Loading Throughput")
plt.xticks(rotation=20)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "rels_per_sec.png", dpi=200)
plt.close()


# ---------------------------------------------------------
# 4. Traversal P50
# ---------------------------------------------------------

hops = ["1_hop", "2_hop", "3_hop"]

plt.figure(figsize=(10, 6))

for platform in platforms:
    values = [
        get_result(platform)["traversals"][hop]["p50"]
        for hop in hops
    ]

    plt.plot(
        [1, 2, 3],
        values,
        marker="o",
        label=platform
    )

plt.xlabel("Traversal Hops")
plt.ylabel("Latency P50 (ms)")
plt.title("Traversal Latency P50")
plt.xticks([1, 2, 3])
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "traversal_p50.png", dpi=200)
plt.close()


# ---------------------------------------------------------
# 5. Traversal P95
# ---------------------------------------------------------

plt.figure(figsize=(10, 6))

for platform in platforms:
    values = [
        get_result(platform)["traversals"][hop]["p95"]
        for hop in hops
    ]

    plt.plot(
        [1, 2, 3],
        values,
        marker="o",
        label=platform
    )

plt.xlabel("Traversal Hops")
plt.ylabel("Latency P95 (ms)")
plt.title("Traversal Latency P95")
plt.xticks([1, 2, 3])
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "traversal_p95.png", dpi=200)
plt.close()


# ---------------------------------------------------------
# 6. Lookup and Aggregation Latency
# ---------------------------------------------------------

categories = [
    "Point Lookup",
    "Filtered Lookup",
    "Aggregation"
]

plt.figure(figsize=(11, 6))

x = list(range(len(categories)))
width = 0.2

for i, platform in enumerate(platforms):
    result = get_result(platform)

    values = [
        result["lookups"]["point_lookup"]["p50"],
        result["lookups"]["filtered_lookup"]["p50"],
        result["aggregations"]["count_by_rel_type"]["p50"]
    ]

    positions = [
        value + (i - 1.5) * width
        for value in x
    ]

    plt.bar(
        positions,
        values,
        width=width,
        label=platform
    )

plt.xlabel("Workload")
plt.ylabel("Latency P50 (ms)")
plt.title("Lookup and Aggregation Latency")
plt.xticks(x, categories)
plt.legend()
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "lookup_aggregation.png", dpi=200)
plt.close()


# ---------------------------------------------------------
# 7. Mixed Workload QPS
# ---------------------------------------------------------

clients = ["1_clients", "10_clients", "40_clients"]

plt.figure(figsize=(10, 6))

for platform in platforms:
    values = [
        get_result(platform)["mixed"][client]["qps"]
        for client in clients
    ]

    plt.plot(
        [1, 10, 40],
        values,
        marker="o",
        label=platform
    )

plt.xlabel("Concurrent Clients")
plt.ylabel("Queries per Second (QPS)")
plt.title("Mixed Read/Write Throughput")
plt.xticks([1, 10, 40])
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "mixed_qps.png", dpi=200)
plt.close()


print("Graph generation completed.")
print(f"Graphs saved to: {OUTPUT_DIR}")
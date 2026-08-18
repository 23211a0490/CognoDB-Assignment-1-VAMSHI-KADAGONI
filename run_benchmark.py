#!/usr/bin/env python3
"""
Orchestrates the full benchmark suite against one or more platforms.

Usage:
    python run_benchmark.py --all
    python run_benchmark.py --platform cognodb --platform neo4j_aura
    python run_benchmark.py --all --mixed-concurrency 1,10,40
"""
import argparse
import json
import os
import sys
import traceback
import time
from datetime import datetime, timezone

from dotenv import load_dotenv

from workloads import traversals, lookups, aggregations, mixed, footprint

load_dotenv()

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
RESULTS_DIR = os.path.join(HERE, "results")

PLATFORM_FACTORIES = {
    "cognodb": lambda: __import__("platforms.cognodb", fromlist=["CognoDBPlatform"]).CognoDBPlatform(),
    "neo4j_aura": lambda: __import__("platforms.neo4j_aura", fromlist=["Neo4jAuraPlatform"]).Neo4jAuraPlatform(),
    "memgraph": lambda: __import__("platforms.memgraph", fromlist=["MemgraphPlatform"]).MemgraphPlatform(),
    "arangodb": lambda: __import__("platforms.arangodb", fromlist=["ArangoDBPlatform"]).ArangoDBPlatform(),
    
}


def run_one_platform(name, factory, args):
    print(f"\n{'=' * 60}\n{name}\n{'=' * 60}")
    result = {"platform": name, "started_at": datetime.now(timezone.utc).isoformat()}
    try:
        p = factory()
        p.connect()

        print("Clearing existing data...")
        p.clear()

        print("Loading dataset...")
        load_stats = p.load(
            os.path.join(DATA_DIR, "nodes.csv"), os.path.join(DATA_DIR, "edges.csv")
        )
        result["load"] = load_stats
        print(f"  {load_stats}")

        print("Creating indexes...")
        result["indexed_properties"] = p.create_indexes()

        # Reconnect before benchmark workloads
        print("Reconnecting before benchmark workloads...")
        p.close()

        
        time.sleep(10)

        p.connect()

        print("Sampling start node IDs...")
        start_ids = p.sample_node_ids(100)
        if not start_ids:
            raise RuntimeError("sample_node_ids returned no IDs -- was the load successful?")

        print("Running traversal workload...")
        result["traversals"] = traversals.run(
            p, start_ids, iterations=args.iterations, warmup=args.warmup
        )

        print("Running lookup workload...")
        result["lookups"] = lookups.run(
            p, start_ids, iterations=args.iterations, warmup=args.warmup
        )

        print("Running aggregation workload...")
        result["aggregations"] = aggregations.run(
            p, iterations=args.iterations, warmup=args.warmup
        )

        print("Running mixed read/write workload...")
        result["mixed"] = mixed.run(
            factory,
            start_ids,
            concurrency_levels=args.mixed_concurrency,
            duration_seconds=args.mixed_duration,
        )

        print("Collecting footprint...")
        result["footprint"] = footprint.run(p)

        p.close()
        result["status"] = "ok"

    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        print(f"  FAILED: {e}", file=sys.stderr)

    result["finished_at"] = datetime.now(timezone.utc).isoformat()
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--platform", action="append", choices=PLATFORM_FACTORIES.keys())
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--iterations", type=int, default=int(os.environ.get("WORKLOAD_ITERATIONS", 100)))
    ap.add_argument("--warmup", type=int, default=int(os.environ.get("WARMUP_ITERATIONS", 10)))
    ap.add_argument(
        "--mixed-concurrency",
        type=lambda s: [int(x) for x in s.split(",")],
        default=[int(x) for x in os.environ.get("MIXED_CONCURRENCY_LEVELS", "1,10,40").split(",")],
    )
    ap.add_argument(
        "--mixed-duration", type=int, default=int(os.environ.get("MIXED_DURATION_SECONDS", 30))
    )
    args = ap.parse_args()

    if not args.all and not args.platform:
        ap.error("pass --all or one or more --platform NAME")

    targets = list(PLATFORM_FACTORIES.keys()) if args.all else args.platform

    nodes_csv = os.path.join(DATA_DIR, "nodes.csv")
    if not os.path.exists(nodes_csv):
        ap.error(f"{nodes_csv} not found -- run data/prepare_dataset.py first")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    all_results = []
    for name in targets:
        res = run_one_platform(name, PLATFORM_FACTORIES[name], args)
        all_results.append(res)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = os.path.join(RESULTS_DIR, f"run_{ts}.json")
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()

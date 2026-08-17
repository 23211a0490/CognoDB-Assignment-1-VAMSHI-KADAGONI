"""
Downloads the SNAP soc-Pokec social network edge list and BFS-samples it down
to a size that fits a 1 GB / 256 MB free-tier graph database instance.

Why BFS sampling instead of uniform random edge sampling: uniform random
subsampling of edges destroys multi-hop connectivity (most sampled nodes end
up with degree 0 or 1), which would make the 2-hop/3-hop traversal workload
meaningless. A BFS sample seeded from a handful of random nodes preserves
realistic local neighborhood structure.

Usage:
    python data/prepare_dataset.py --target-edges 350000 --seed 42

Outputs (relative to this file's directory):
    nodes.csv              id:ID,label
    edges.csv              :START_ID,:END_ID,:TYPE
    dataset_manifest.json  exact counts + seed, for reproducibility
"""
import argparse
import gzip
import json
import os
import random
import sys
from collections import defaultdict, deque

import requests
from tqdm import tqdm

SNAP_URL = "https://snap.stanford.edu/data/soc-pokec-relationships.txt.gz"
HERE = os.path.dirname(os.path.abspath(__file__))
RAW_PATH = os.path.join(HERE, "soc-pokec-relationships.txt.gz")


def download_raw(force: bool = False) -> str:
    if os.path.exists(RAW_PATH) and not force:
        print(f"Raw file already present at {RAW_PATH}, skipping download.")
        return RAW_PATH
    print(f"Downloading {SNAP_URL} ...")
    resp = requests.get(SNAP_URL, stream=True, timeout=60)
    resp.raise_for_status()
    total = int(resp.headers.get("content-length", 0))
    with open(RAW_PATH, "wb") as f, tqdm(total=total, unit="B", unit_scale=True) as bar:
        for chunk in resp.iter_content(chunk_size=1 << 20):
            f.write(chunk)
            bar.update(len(chunk))
    return RAW_PATH


def build_adjacency(raw_path: str):
    """Streams the edge list once and builds an out-adjacency map."""
    adj = defaultdict(list)
    n_edges_total = 0
    with gzip.open(raw_path, "rt") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            a, b = line.split("\t")
            adj[a].append(b)
            n_edges_total += 1
    print(f"Full graph: {len(adj)} source nodes, {n_edges_total} directed edges.")
    return adj


def bfs_sample(adj, target_edges: int, seed: int, seed_nodes: int = 25):
    rng = random.Random(seed)
    all_nodes = list(adj.keys())
    frontier = deque(rng.sample(all_nodes, min(seed_nodes, len(all_nodes))))
    visited = set(frontier)
    sampled_edges = []

    with tqdm(total=target_edges, desc="BFS sampling edges") as bar:
        while frontier and len(sampled_edges) < target_edges:
            node = frontier.popleft()
            for nbr in adj.get(node, []):
                sampled_edges.append((node, nbr))
                bar.update(1)
                if nbr not in visited:
                    visited.add(nbr)
                    frontier.append(nbr)
                if len(sampled_edges) >= target_edges:
                    break

    sampled_nodes = set()
    for a, b in sampled_edges:
        sampled_nodes.add(a)
        sampled_nodes.add(b)
    return sampled_nodes, sampled_edges


def write_csvs(nodes, edges, out_dir):
    nodes_path = os.path.join(out_dir, "nodes.csv")
    edges_path = os.path.join(out_dir, "edges.csv")

    with open(nodes_path, "w") as f:
        f.write("id:ID,label\n")
        for n in nodes:
            f.write(f"{n},Person\n")

    with open(edges_path, "w") as f:
        f.write(":START_ID,:END_ID,:TYPE\n")
        for a, b in edges:
            f.write(f"{a},{b},FRIEND\n")

    return nodes_path, edges_path


def write_manifest(nodes, edges, seed, target_edges, out_dir):
    degree = defaultdict(int)
    for a, b in edges:
        degree[a] += 1
        degree[b] += 1
    degrees = sorted(degree.values())
    manifest = {
        "source": "SNAP soc-Pokec (https://snap.stanford.edu/data/soc-Pokec.html)",
        "sampling_method": "BFS sample seeded from 25 random nodes",
        "seed": seed,
        "target_edges": target_edges,
        "actual_node_count": len(nodes),
        "actual_edge_count": len(edges),
        "degree_min": degrees[0] if degrees else 0,
        "degree_median": degrees[len(degrees) // 2] if degrees else 0,
        "degree_max": degrees[-1] if degrees else 0,
    }
    path = os.path.join(out_dir, "dataset_manifest.json")
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(json.dumps(manifest, indent=2))
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-edges", type=int, default=350_000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--seed-nodes", type=int, default=25)
    ap.add_argument("--force-download", action="store_true")
    args = ap.parse_args()

    raw_path = download_raw(force=args.force_download)
    adj = build_adjacency(raw_path)
    nodes, edges = bfs_sample(adj, args.target_edges, args.seed, args.seed_nodes)
    print(f"Sampled {len(nodes)} nodes, {len(edges)} edges.")

    nodes_path, edges_path = write_csvs(nodes, edges, HERE)
    write_manifest(nodes, edges, args.seed, args.target_edges, HERE)
    print(f"Wrote {nodes_path} and {edges_path}")


if __name__ == "__main__":
    sys.exit(main())

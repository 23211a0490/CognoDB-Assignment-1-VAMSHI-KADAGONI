# Graph Database Cloud Benchmark — CognoDB vs. 4 Managed/Self-Hosted Alternatives

A reproducible benchmark comparing [CognoDB Cloud](https://cognodb.com) against four other graph
database platforms on identical hardware tiers, an identical dataset, and identical query
workloads.

> **Status of this repo:** methodology, harness, and adapters are complete and runnable. The
> results tables below are templates — run `python run_benchmark.py --all` with your own
> free-tier credentials (see [Setup](#setup)) to populate them with real numbers before
> submitting.

## 1. Platforms compared

| Platform | Tier used | Advertised specs (free/entry tier) | Query language | Driver |
|---|---|---|---|---|
| **CognoDB Cloud** | Free (c0) | 0.5 vCPU (burstable), 256 MB RAM, 1 GB disk | Cypher | `neo4j` driver (Bolt-compatible) |
| **Neo4j AuraDB Free** | Free | 0.5 vCPU (shared/burstable), ~256 MB usable RAM, 1 GB storage | Cypher | `neo4j` driver |
| **Memgraph Cloud** | Free tier | 0.5 vCPU, 256 MB RAM, 1 GB storage (matched via project config) | Cypher (in-memory engine) | `neo4j` driver (Memgraph is Bolt-compatible) |
| **ArangoDB Oasis** | Free trial, smallest tier | 0.5 vCPU / 256 MB / 1 GB (smallest selectable size) | AQL | `python-arango` |
| **JanusGraph** | Self-hosted, Docker | Capped via `--cpus=0.5 --memory=256m`, 1 GB volume | Gremlin | `gremlinpython` |

**Why these five:** CognoDB and Neo4j Aura give a direct Cypher-over-Bolt comparison against the
most widely used managed graph DB. Memgraph adds a second Bolt/Cypher engine but with a very
different (in-memory, C++) execution model, which isolates "database engine" from "query
language" as a variable. ArangoDB tests a genuinely different query language (AQL) and
multi-model storage engine. JanusGraph, self-hosted and explicitly resource-capped with Docker,
lets us include an option that isn't a managed SaaS at all, using the assignment's explicit
allowance for "self-hosted deployments capped to the same resources." Together these span managed
vs. self-hosted, disk-backed vs. in-memory, and three different query languages — while every one
of them runs at the same 0.5 vCPU / 256 MB RAM / 1 GB disk envelope.

**Caveat (state honestly, don't hide):** "same vCPU/RAM" on shared/burstable free tiers is a
*target*, not a guarantee — cloud free tiers throttle unpredictably and you don't control the
underlying host. Record the platform's own published spec (above) and additionally record
observed behavior (e.g. throttling, timeouts) during your run in the Caveats section.

## 2. Dataset

- **Source:** [SNAP soc-Pokec social network](https://snap.stanford.edu/data/soc-Pokec.html) (Stanford Large Network Dataset Collection).
- **Sampling:** the full graph (~1.6M nodes / ~30.6M edges) is too large for a 1 GB / 256 MB
  free-tier instance. `data/prepare_dataset.py` takes a **breadth-first sample seeded from a
  random set of high-degree nodes**, stopping once the sample reaches **~120,000 nodes and
  ~350,000 relationships** (tune via `--target-edges`), then writes:
  - `data/nodes.csv` — `id:ID,label`
  - `data/edges.csv` — `:START_ID,:END_ID,:TYPE`
- BFS sampling (rather than uniform random edge sampling) preserves realistic multi-hop
  connectivity, which matters for the 1/2/3-hop traversal workload — a uniform random subsample
  of edges would artificially shrink hop counts.
- The identical `nodes.csv` / `edges.csv` pair is loaded, unmodified, into all five platforms.
  Loader code per platform lives in `platforms/<name>.py::load()`.

Run once to generate the dataset:
```bash
python data/prepare_dataset.py --target-edges 350000 --seed 42
```
This writes `data/nodes.csv`, `data/edges.csv`, and `data/dataset_manifest.json` (exact node/edge
counts, degree distribution summary, and the seed — for reproducibility).

## 3. Workloads

All defined in `workloads/` and run identically against every platform through the
`BasePlatform` adapter interface (`common/base_platform.py`):

| Workload | File | What it does |
|---|---|---|
| Ingest | `platforms/<name>.py::load()` | Bulk/batched load of nodes + edges; times wall-clock, computes nodes/sec and rels/sec |
| Traversals | `workloads/traversals.py` | 1-hop, 2-hop, 3-hop neighbor expansion from 100 randomly chosen start nodes (same node IDs across platforms), ≥100 iterations each after 10 warm-up iterations |
| Lookups | `workloads/lookups.py` | (a) point lookup by node ID, (b) indexed/filtered lookup by an indexed property; ≥100 iterations after warm-up |
| Aggregations | `workloads/aggregations.py` | `COUNT`/`GROUP BY`-style query: relationship count grouped by type (or label) |
| Mixed workload | `workloads/mixed.py` | Concurrent read/write throughput at 1 / 10 / 40 clients, 80/20 read/write mix, 30-second sustained run per concurrency level, reports queries/sec |
| Footprint | `workloads/footprint.py` | Stored data size / memory usage where the platform's API or console exposes it; otherwise recorded as "not observable" |

All latency workloads report **p50 and p95**, not just mean — per the assignment's requirement.

## 4. Setup

### 4.1 Credentials
Copy `.env.example` to `.env` and fill in the connection details for whichever platforms you've
provisioned. **Never commit `.env`** — it's gitignored. All platform adapters read secrets only
from environment variables, per the assignment's requirement not to commit passwords/URIs.

```bash
cp .env.example .env
# then edit .env
```

### 4.2 Per-platform provisioning (do this once per platform)

- **CognoDB Cloud:** sign up at console.cognodb.com → create a free (c0) instance → copy the
  `bolt+s://...` URI and the one-time password into `.env` as `COGNODB_URI` / `COGNODB_PASSWORD`.
- **Neo4j AuraDB Free:** console.neo4j.io → New Instance → Free → download the auto-generated
  credentials file → `.env` as `NEO4J_AURA_URI` / `NEO4J_AURA_PASSWORD`.
- **Memgraph Cloud:** console.memgraphcloud.com → create free project → `.env` as
  `MEMGRAPH_URI` / `MEMGRAPH_PASSWORD`.
- **ArangoDB Oasis:** dashboard.arangodb.cloud → free trial → smallest deployment size → `.env`
  as `ARANGO_ENDPOINT` / `ARANGO_PASSWORD`.
- **JanusGraph (self-hosted, capped):**
  ```bash
  docker run -d --name janusgraph --cpus=0.5 --memory=256m \
    -p 8182:8182 -v janusgraph_data:/var/lib/janusgraph \
    janusgraph/janusgraph:latest
  ```
  No credentials needed by default; `.env`'s `JANUSGRAPH_URL` just points at `ws://localhost:8182/gremlin`.

### 4.3 Install dependencies
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 5. Running the benchmark

```bash
# Generate the dataset once
python data/prepare_dataset.py --target-edges 350000 --seed 42

# Run everything against every platform configured in .env
python run_benchmark.py --all

# Or target one platform at a time, e.g. while debugging
python run_benchmark.py --platform cognodb

# Sweep concurrency levels explicitly for the mixed workload
python run_benchmark.py --all --mixed-concurrency 1,10,40
```

Each run appends a timestamped JSON file to `results/` and regenerates
`results/summary_tables.md` (the source for the tables in Section 6 below) via
`python results/render_tables.py`.

## 6. Results

*(Fill in after running — `results/render_tables.py` generates these automatically from the JSON
run files, so you can paste its output here directly.)*

### 6.1 Data loading

| Platform | Nodes/sec | Rels/sec | Total load time |
|---|---|---|---|
| CognoDB | | | |
| Neo4j AuraDB Free | | | |
| Memgraph Cloud | | | |
| ArangoDB Oasis | | | |
| JanusGraph (capped) | | | |

### 6.2 Traversals (p50 / p95, ms)

| Platform | 1-hop | 2-hop | 3-hop |
|---|---|---|---|
| CognoDB | / | / | / |
| Neo4j AuraDB Free | / | / | / |
| Memgraph Cloud | / | / | / |
| ArangoDB Oasis | / | / | / |
| JanusGraph (capped) | / | / | / |

### 6.3 Lookups (p50 / p95, ms)

| Platform | Point lookup | Indexed/filtered lookup | Indexed properties |
|---|---|---|---|
| CognoDB | / | / | |
| Neo4j AuraDB Free | / | / | |
| Memgraph Cloud | / | / | |
| ArangoDB Oasis | / | / | |
| JanusGraph (capped) | / | / | |

### 6.4 Aggregations (p50 / p95, ms)

| Platform | Count by relationship type |
|---|---|
| CognoDB | / |
| Neo4j AuraDB Free | / |
| Memgraph Cloud | / |
| ArangoDB Oasis | / |
| JanusGraph (capped) | / |

### 6.5 Mixed workload throughput (queries/sec, 80/20 read/write)

| Platform | 1 client | 10 clients | 40 clients |
|---|---|---|---|
| CognoDB | | | |
| Neo4j AuraDB Free | | | |
| Memgraph Cloud | | | |
| ArangoDB Oasis | | | |
| JanusGraph (capped) | | | |

### 6.6 Footprint

| Platform | Stored data size | Memory usage | Notes |
|---|---|---|---|
| CognoDB | | | |
| Neo4j AuraDB Free | | | |
| Memgraph Cloud | | | |
| ArangoDB Oasis | | | |
| JanusGraph (capped) | | | |

## 7. Analysis

*(Fill in after running. Suggested structure: (1) which platform(s) led on ingest and why —
usually driven by bulk-import API availability vs. driver-batched inserts; (2) traversal latency
trends as hop depth increases, and whether in-memory (Memgraph) vs. disk-backed engines diverge as
expected; (3) whether AQL's multi-model engine and Gremlin's traversal-step model show different
scaling behavior than Cypher pattern-matching on the same hop workload; (4) how throughput holds
up from 1→10→40 concurrent clients on 0.5 vCPU — this is usually where free-tier throttling shows
up most visibly; (5) anywhere CognoDB specifically over/under-performs its Neo4j-compatible peer
Aura, since that's the most directly comparable pair here.)*

## 8. Caveats and known limitations

*(Fill in honestly as you encounter them — expected categories: free-tier throttling/timeouts,
network latency variance since clients aren't co-located with every provider's region, query
translation differences between Cypher/AQL/Gremlin for "equivalent" queries, any failed runs and
how they were handled, cold-start vs. warm numbers if included.)*

## 9. Repo layout

```
.
├── README.md
├── requirements.txt
├── .env.example
├── data/
│   └── prepare_dataset.py       # downloads + BFS-samples SNAP soc-Pokec
├── common/
│   ├── base_platform.py         # adapter interface every platform implements
│   └── metrics.py                # timing, percentile, results-JSON helpers
├── platforms/
│   ├── cognodb.py
│   ├── neo4j_aura.py
│   ├── memgraph.py
│   ├── arangodb.py
│   └── janusgraph.py
├── workloads/
│   ├── traversals.py
│   ├── lookups.py
│   ├── aggregations.py
│   ├── mixed.py
│   └── footprint.py
├── run_benchmark.py              # CLI orchestrator
└── results/
    ├── render_tables.py
    └── *.json                    # one per run, timestamped
```

## 10. Reproducing this benchmark

1. Clone this repo.
2. Provision free-tier instances on each platform per [Setup](#setup).
3. `pip install -r requirements.txt`
4. `python data/prepare_dataset.py --target-edges 350000 --seed 42`
5. `python run_benchmark.py --all`
6. `python results/render_tables.py` to regenerate the tables above from your run's JSON output.

No step requires anything beyond free-tier accounts and the commands above.

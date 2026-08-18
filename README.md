# Graph Database Cloud Benchmark — CognoDB vs Neo4j AuraDB vs Memgraph vs ArangoDB vs FalkorDB

A reproducible benchmark comparing five graph database platforms using the same
dataset, equivalent workloads, and comparable resource tiers.

The benchmark evaluates:

- CognoDB Cloud
- Neo4j AuraDB Free
- Memgraph Cloud
- ArangoDB Oasis
- FalkorDB Cloud

The project measures data loading performance, graph traversal latency,
point lookups, aggregations, mixed read/write throughput, and database
footprint where available.

---

## 1. Platforms Compared

| Platform | Tier Used | Query Language | Driver |
|---|---|---|---|
| **CognoDB Cloud** | Free (c0) | Cypher | `neo4j` driver |
| **Neo4j AuraDB Free** | Free | Cypher | `neo4j` driver |
| **Memgraph Cloud** | Free tier | Cypher | `neo4j` driver |
| **ArangoDB Oasis** | Free/entry tier | AQL | `python-arango` |
| **FalkorDB Cloud** | Free/entry tier | Cypher | `falkordb` Python client |

### Why These Platforms?

The benchmark includes several different graph database architectures and
query engines.

**CognoDB and Neo4j AuraDB** provide a direct comparison because both support
Cypher and Bolt-compatible connectivity.

**Memgraph** provides another Cypher-based graph database with an
in-memory-oriented execution model.

**ArangoDB** provides a different query language, AQL, and a multi-model
database architecture.

**FalkorDB** provides a Redis-based graph database engine supporting
Cypher queries.

Together, these platforms provide a useful comparison of graph database
performance across different architectures and implementations.

> **Note:** Cloud free-tier resources are not perfectly identical in practice.
> Shared infrastructure, network latency, CPU throttling, and provider-side
> resource management can affect benchmark results. Therefore, results should
> be interpreted as measurements under the tested configurations rather than
> absolute hardware-normalized performance.

---

# 2. Dataset

The benchmark uses the **SNAP soc-Pokec social network dataset** from the
Stanford Large Network Dataset Collection.

Source:

https://snap.stanford.edu/data/soc-Pokec.html

The original dataset is much larger than the storage and memory limits of
small/free-tier database deployments. Therefore, a BFS-based sample was
generated.

### Dataset Configuration

| Property | Value |
|---|---|
| Dataset | SNAP soc-Pokec |
| Sampling method | BFS sampling |
| Random seed | 42 |
| Target relationships | 250,000 |
| Actual nodes | 135,836 |
| Actual relationships | 250,000 |

The dataset was generated using:

```bash
python data/prepare_dataset.py --target-edges 250000 --seed 42
# Graph Database Cloud Benchmark

A reproducible benchmark comparing **CognoDB Cloud**, **Neo4j AuraDB**, **Memgraph Cloud**, **ArangoDB Oasis**, and **FalkorDB Cloud** using the same dataset, benchmark workloads, and comparable cloud resource tiers.

The benchmark evaluates data loading, graph traversal, point lookups, filtered lookups, aggregation queries, concurrent read/write throughput, and database footprint where observable.

---

## 1. Platforms Compared

| Platform | Tier | Query Language | Driver |
|---|---|---|---|
| **CognoDB Cloud** | Free (c0) | Cypher | Neo4j Bolt driver |
| **Neo4j AuraDB** | Free | Cypher | Neo4j driver |
| **Memgraph Cloud** | Free tier | Cypher | Neo4j Bolt driver |
| **ArangoDB Oasis** | Smallest/free tier | AQL | python-arango |
| **FalkorDB Cloud** | Cloud tier | Cypher | FalkorDB Python client |

The benchmark compares multiple graph database architectures using a common dataset and logically equivalent workloads.

---

# 2. Dataset

The benchmark uses the **SNAP soc-Pokec social network dataset**.

Source:

https://snap.stanford.edu/data/soc-Pokec.html

The dataset was sampled using a breadth-first search (BFS) strategy to produce a graph suitable for the available cloud database tiers.

### Final Dataset

| Property | Value |
|---|---:|
| Sampling method | BFS |
| Random seed | 42 |
| Target edges | **250,000** |
| Actual edges | **250,000** |
| Actual nodes | **135,836** |
| Minimum degree | 1 |
| Median degree | 1 |
| Maximum degree | 7,598 |

The exact dataset information is stored in:

```text
data/dataset_manifest.json
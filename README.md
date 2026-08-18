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

**Source:**  
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

3. Benchmark Workloads

The benchmark measures the following workloads:

Workload	Description
Data Loading	Measures node and relationship insertion speed
1-hop Traversal	Expands one level from a starting node
2-hop Traversal	Expands two levels from a starting node
3-hop Traversal	Expands three levels from a starting node
Point Lookup	Looks up a node using its ID
Filtered Lookup	Performs an indexed property lookup
Aggregation	Counts relationships grouped by relationship type
Mixed Workload	Concurrent 80/20 read/write workload
Footprint	Records storage/memory information when available

Latency results are reported using p50 and p95.

The mixed workload tests:

1 client
10 clients
40 clients
4. Benchmark Results

The following tables are generated from the benchmark results stored in results/summary_tables.md.

### Data loading

| Platform | Nodes/sec | Rels/sec | Total load time |
|---|---:|---:|---:|
| CognoDB | 184.15 | 338.93 | 737.62 s |
| Neo4j AuraDB | 824.17 | 1516.84 | 164.82 s |
| Memgraph Cloud | 450.71 | 829.51 | 301.38 s |
| ArangoDB Oasis | 731.20 | 1345.73 | 185.77 s |
| FalkorDB Cloud | 979.02 | 1801.84 | 138.75 s |

### Traversals (p50 / p95, ms)

| Platform | 1-hop | 2-hop | 3-hop |
|---|---:|---:|---:|
| CognoDB | 247.54 / 300.28 | 248.99 / 314.50 | 271.38 / 974.66 |
| Neo4j AuraDB | 55.35 / 56.79 | 55.65 / 60.32 | 56.80 / 70.73 |
| Memgraph Cloud | 147.21 / 150.67 | 147.73 / 151.09 | 148.69 / 163.03 |
| ArangoDB Oasis | 306.60 / 558.87 | 298.60 / 409.70 | 261.64 / 349.83 |
| FalkorDB Cloud | 17.20 / 71.78 | 16.90 / 19.99 | 16.72 / 18.68 |

### Lookups (p50 / p95, ms)

| Platform | Point lookup | Indexed/filtered lookup | Indexed properties |
|---|---:|---:|---|
| CognoDB | 248.19 / 287.67 | 248.26 / 289.11 | Person.id |
| Neo4j AuraDB | 55.46 / 56.77 | 55.23 / 56.61 | Person.id |
| Memgraph Cloud | 147.71 / 179.02 | 147.66 / 151.29 | Person.id |
| ArangoDB Oasis | 306.19 / 359.02 | 306.58 / 408.45 | people._key (built-in primary index) |
| FalkorDB Cloud | 16.34 / 18.11 | 16.97 / 18.17 | Person.id |

### Aggregations (p50 / p95, ms)

| Platform | Count by relationship type |
|---|---:|
| CognoDB | 1691.33 / 3005.80 |
| Neo4j AuraDB | 92.62 / 105.62 |
| Memgraph Cloud | 230.80 / 253.52 |
| ArangoDB Oasis | 475.92 / 924.66 |
| FalkorDB Cloud | 417.91 / 470.94 |

### Mixed workload throughput (queries/sec)

| Platform | 1 client | 10 clients | 40 clients |
|---|---:|---:|---:|
| CognoDB | 1.74 | 16.60 | 41.38 |
| Neo4j AuraDB | 17.10 | 172.19 | 685.67 |
| Memgraph Cloud | 6.16 | 64.25 | 261.90 |
| ArangoDB Oasis | 3.07 | 31.59 | 104.44 |
| FalkorDB Cloud | 49.59 | 529.86 | 1667.54 |

### Footprint

| Platform | Stored data size | Memory usage |
|---|---|---|
| CognoDB | not observable | not observable |
| Neo4j AuraDB | not observable | not observable |
| Memgraph Cloud | not observable | not observable |
| ArangoDB Oasis | not observable | see ArangoDB Oasis dashboard |
| FalkorDB Cloud | not observable | not observable |


5. Performance Summary

The benchmark results show measurable differences between the five tested platforms.

Data Loading

Based on the measured results, FalkorDB Cloud achieved the highest node ingestion rate and relationship ingestion rate, while also recording the shortest total loading time.

Graph Traversals

FalkorDB Cloud recorded the lowest p50 traversal latency across the tested 1-hop, 2-hop, and 3-hop workloads.

Neo4j AuraDB also demonstrated consistently low traversal latency compared with the other platforms.

Lookups

FalkorDB Cloud recorded the lowest point-lookup latency in the measured workload, followed by Neo4j AuraDB.

Aggregations

Neo4j AuraDB recorded the lowest p50 aggregation latency among the five tested platforms.

Mixed Read/Write Workload

FalkorDB Cloud achieved the highest measured throughput at 1, 10, and 40 concurrent clients.

The measured results should be interpreted as results for the tested configurations and network conditions rather than universal rankings.

6. Comparison Graphs

The benchmark graphs are stored in:

results/graphs/
Load Time

Nodes Per Second

Relationships Per Second

Traversal Latency — p50

Traversal Latency — p95

Lookup and Aggregation

Mixed Workload QPS

7. Repository Structure
.
├── README.md
├── LICENSE
├── requirements.txt
├── .env.example
├── run_benchmark.py
│
├── common/
│   ├── base_platform.py
│   └── metrics.py
│
├── data/
│   ├── prepare_dataset.py
│   ├── dataset_manifest.json
│   ├── nodes.csv
│   └── edges.csv
│
├── platforms/
│   ├── cognodb.py
│   ├── neo4j_aura.py
│   ├── memgraph.py
│   ├── arangodb.py
│   └── falkordb.py
│
├── workloads/
│   ├── traversals.py
│   ├── lookups.py
│   ├── aggregations.py
│   ├── mixed.py
│   └── footprint.py
│
└── results/
    ├── summary.json
    ├── summary_tables.md
    ├── render_tables.py
    └── graphs/
        ├── load_time.png
        ├── nodes_per_sec.png
        ├── rels_per_sec.png
        ├── traversal_p50.png
        ├── traversal_p95.png
        ├── lookup_aggregation.png
        └── mixed_qps.png
8. Reproducing the Benchmark
Create the Python environment
python -m venv .venv
Activate on Windows PowerShell
.venv\Scripts\Activate.ps1
Install dependencies
pip install -r requirements.txt
Configure credentials

Create a .env file containing the required database connection details.

The .env file is excluded from Git and must never be committed.

Generate the dataset
python data/prepare_dataset.py --target-edges 250000 --seed 42
Run the benchmark
python run_benchmark.py --all
Generate result tables and graphs
python results/render_tables.py
Generate this README
python generate_readme.py
9. Reproducibility

The benchmark uses:

The same dataset for every platform
The same random seed
The same workload definitions
The same iteration methodology
The same concurrency levels
p50 and p95 latency measurements
The same sampled start-node methodology

The dataset manifest provides the exact node and relationship counts used for the benchmark.

10. Limitations

The results are subject to several limitations:

Cloud providers may use shared or burstable infrastructure.
Network latency between the benchmark machine and each cloud service may differ.
Different database engines use different query execution architectures.
Query languages are not internally identical even when workloads are logically equivalent.
Free-tier services may throttle or change performance over time.
Footprint information may not be available through public APIs or dashboards.
The benchmark represents the tested dataset and workload rather than every possible graph workload.

Therefore, the results should be treated as a reproducible benchmark of the tested configurations rather than a universal ranking of graph database systems.

11. Conclusion

This benchmark provides a reproducible comparison of five graph database platforms using a common social-network dataset and a consistent workload suite.

The benchmark evaluates:

Data ingestion performance
Multi-hop graph traversal
Point and filtered lookups
Aggregation queries
Concurrent read/write throughput
Storage and memory footprint where observable

The benchmark results, tables, and comparison graphs are included in the repository for transparency and reproducibility.

Project Status

Benchmark completed for five platforms:

CognoDB Cloud
Neo4j AuraDB
Memgraph Cloud
ArangoDB Oasis
FalkorDB Cloud


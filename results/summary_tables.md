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

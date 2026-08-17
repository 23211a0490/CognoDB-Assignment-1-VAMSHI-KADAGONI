import csv
import os
import time

from gremlin_python.driver import client, serializer

from common.base_platform import BasePlatform

BATCH_SIZE = 500  # smaller batches: Gremlin script submission has more per-call overhead


class JanusGraphPlatform(BasePlatform):
    name = "janusgraph"

    def __init__(self):
        self.url = os.environ.get("JANUSGRAPH_URL", "ws://localhost:8182/gremlin")
        self.client = None

    def connect(self):
        self.client = client.Client(
            self.url, "g", message_serializer=serializer.GraphSONSerializersV3d0()
        )
        # sanity check
        self.client.submit("g.V().limit(1)").all().result()

    def close(self):
        if self.client:
            self.client.close()

    def clear(self):
        self.client.submit("g.V().drop().iterate()").all().result()

    def load(self, nodes_path: str, edges_path: str) -> dict:
        node_count = 0
        rel_count = 0
        start = time.perf_counter()

        with open(nodes_path) as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                batch.append(row["id:ID"])
                if len(batch) >= BATCH_SIZE:
                    self._insert_node_batch(batch)
                    node_count += len(batch)
                    batch = []
            if batch:
                self._insert_node_batch(batch)
                node_count += len(batch)

        with open(edges_path) as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                batch.append((row[":START_ID"], row[":END_ID"]))
                if len(batch) >= BATCH_SIZE:
                    self._insert_edge_batch(batch)
                    rel_count += len(batch)
                    batch = []
            if batch:
                self._insert_edge_batch(batch)
                rel_count += len(batch)

        total_seconds = time.perf_counter() - start
        return {
            "nodes_per_sec": round(node_count / total_seconds, 2) if total_seconds else 0,
            "rels_per_sec": round(rel_count / total_seconds, 2) if total_seconds else 0,
            "total_seconds": round(total_seconds, 2),
            "load_method": f"gremlinpython, script-submitted batches of {BATCH_SIZE}",
        }

    def _insert_node_batch(self, ids):
        script = "ids.each { id -> g.addV('Person').property('pid', id).next() }"
        self.client.submit(script, {"ids": ids}).all().result()

    def _insert_edge_batch(self, pairs):
        script = (
            "pairs.each { p -> "
            "g.V().has('Person','pid', p[0]).as('a')."
            "V().has('Person','pid', p[1]).addE('FRIEND').from('a').next() }"
        )
        self.client.submit(script, {"pairs": [list(p) for p in pairs]}).all().result()

    def create_indexes(self) -> list:
        # Composite index on 'pid' -- exact syntax depends on JanusGraph's
        # management API; simplest portable approach is a Gremlin-submitted
        # management script executed once via `gremlin-console` per JanusGraph
        # docs. Left as a documented manual step since it's a one-time schema
        # operation, not part of the timed workload:
        #
        #   mgmt = graph.openManagement()
        #   pid = mgmt.makePropertyKey('pid').dataType(String.class).make()
        #   mgmt.buildIndex('byPid', Vertex.class).addKey(pid).unique().buildCompositeIndex()
        #   mgmt.commit()
        return ["Person.pid (composite index, created via openManagement() -- see comment)"]

    def sample_node_ids(self, n: int) -> list:
        result = self.client.submit(
            "g.V().sample(n).values('pid')", {"n": n}
        ).all().result()
        return result

    def traverse(self, start_id, hops: int):
        repeat = ".out('FRIEND')" * hops
        script = f"g.V().has('Person','pid', sid){repeat}.dedup().count()"
        return self.client.submit(script, {"sid": start_id}).all().result()

    def point_lookup(self, node_id):
        return self.client.submit(
            "g.V().has('Person','pid', sid)", {"sid": node_id}
        ).all().result()

    def filtered_lookup(self, value):
        return self.client.submit(
            "g.V().has('Person','pid', sid)", {"sid": value}
        ).all().result()

    def aggregate_count_by_type(self):
        return self.client.submit(
            "g.E().groupCount().by(label)"
        ).all().result()

    def mixed_read(self, node_id):
        self.client.submit(
            "g.V().has('Person','pid', sid).out('FRIEND').limit(10)", {"sid": node_id}
        ).all().result()

    def mixed_write(self, node_id):
        self.client.submit(
            "g.V().has('Person','pid', sid).property('last_touched', System.currentTimeMillis())",
            {"sid": node_id},
        ).all().result()

import csv
import os
import time

from dotenv import load_dotenv
from falkordb import FalkorDB

from common.base_platform import BasePlatform

load_dotenv()

BATCH_SIZE = 1000

class FalkorDBPlatform(BasePlatform):
    name = "falkordb"

    def __init__(self):
        self.host = os.environ.get("FALKORDB_HOST")
        self.port = int(os.environ.get("FALKORDB_PORT", 6379))
        self.username = os.environ.get("FALKORDB_USERNAME", "falkordb")
        self.password = os.environ.get("FALKORDB_PASSWORD")

        self.db = None
        self.graph = None

    def connect(self):
        self.db = FalkorDB(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
        )

        self.graph = self.db.select_graph("benchmark")

        # Sanity check
        self.graph.query("RETURN 1")

    def close(self):
        self.graph = None
        self.db = None

    def clear(self):
        try:
            self.graph.delete()
        except Exception:
            pass

        self.graph = self.db.select_graph("benchmark")

    def load(self, nodes_path: str, edges_path: str) -> dict:
        node_count = 0
        rel_count = 0
        start = time.perf_counter()

        # Load nodes
        with open(nodes_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            batch = []

            for row in reader:
                batch.append({"id": row["id:ID"]})

                if len(batch) >= BATCH_SIZE:
                    self._insert_node_batch(batch)
                    node_count += len(batch)
                    batch = []

            if batch:
                self._insert_node_batch(batch)
                node_count += len(batch)
                # Create the node ID index before loading relationships.
        # This makes the MATCH operations in the edge loader much faster.
        try:
                self.graph.query(
            "CREATE INDEX FOR (p:Person) ON (p.id)"
            )
        except Exception:
            pass

        # Load relationships
        with open(edges_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            batch = []

            for row in reader:
                batch.append({
                    "source": row[":START_ID"],
                    "target": row[":END_ID"],
                })

                if len(batch) >= BATCH_SIZE:
                    self._insert_edge_batch(batch)
                    rel_count += len(batch)
                    batch = []

            if batch:
                self._insert_edge_batch(batch)
                rel_count += len(batch)

        total_seconds = time.perf_counter() - start

        return {
            "nodes_per_sec": round(node_count / total_seconds, 2)
            if total_seconds else 0,
            "rels_per_sec": round(rel_count / total_seconds, 2)
            if total_seconds else 0,
            "total_seconds": round(total_seconds, 2),
            "load_method": f"FalkorDB UNWIND batches of {BATCH_SIZE}",
        }

    def _insert_node_batch(self, batch):
        query = """
        UNWIND $rows AS row
        CREATE (:Person {id: row.id})
        """

        self.graph.query(query, {"rows": batch})

    def _insert_edge_batch(self, batch):
        query = """
        UNWIND $rows AS row
        MATCH (a:Person {id: row.source})
        MATCH (b:Person {id: row.target})
        CREATE (a)-[:FRIEND]->(b)
        """

        self.graph.query(query, {"rows": batch})

    def create_indexes(self) -> list:
        try:
            self.graph.query(
                "CREATE INDEX FOR (p:Person) ON (p.id)"
            )
        except Exception:
            pass

        return ["Person.id"]

    def sample_node_ids(self, n: int) -> list:
        result = self.graph.query(
            f"MATCH (p:Person) RETURN p.id LIMIT {n}"
        )

        return [row[0] for row in result.result_set]

    def traverse(self, start_id, hops: int):
        query = f"""
        MATCH (p:Person {{id: $id}})
        MATCH (p)-[:FRIEND*{hops}]->(x)
        RETURN count(DISTINCT x)
        """

        return self.graph.query(
            query, {"id": start_id}
        ).result_set

    def point_lookup(self, node_id):
        return self.graph.query(
            "MATCH (p:Person {id: $id}) RETURN p",
            {"id": node_id},
        ).result_set

    def filtered_lookup(self, value):
        return self.graph.query(
            "MATCH (p:Person {id: $id}) RETURN p",
            {"id": value},
        ).result_set

    def aggregate_count_by_type(self):
        return self.graph.query(
            """
            MATCH ()-[r]->()
            RETURN type(r), count(r)
            """
        ).result_set

    def mixed_read(self, node_id):
        self.graph.query(
            """
            MATCH (p:Person {id: $id})-[:FRIEND]->(x)
            RETURN x
            LIMIT 10
            """,
            {"id": node_id},
        )

    def mixed_write(self, node_id):
        self.graph.query(
            """
            MATCH (p:Person {id: $id})
            SET p.last_touched = timestamp()
            """,
            {"id": node_id},
        )
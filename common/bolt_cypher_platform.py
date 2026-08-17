"""
Shared implementation for any Bolt+Cypher speaking platform (CognoDB,
Neo4j AuraDB, Memgraph). All three are driven identically through the
official `neo4j` Python driver -- per the assignment's note that CognoDB
requires "no other code changes" beyond pointing the driver at its URI.

Subclasses just supply connection details and a `name`.
"""
import csv
import random
import time



from neo4j import GraphDatabase

from common.base_platform import BasePlatform

BATCH_SIZE = 200


class BoltCypherPlatform(BasePlatform):
    def __init__(self, uri: str, user: str, password: str, name: str):
        if not uri or not password:
            raise RuntimeError(
                f"{name}: missing URI or password. Check your .env file."
            )
        self.uri = uri
        self.user = user
        self.password = password
        self.name = name
        self.driver = None
        self._node_ids_cache = None

    def connect(self):
        self.driver = GraphDatabase.driver(
        self.uri,
        auth=(self.user, self.password),
        )
        self.driver.verify_connectivity()

    def close(self):
        if self.driver:
            self.driver.close()

    def clear(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def load(self, nodes_path: str, edges_path: str) -> dict:
        node_count = 0
        rel_count = 0
        start = time.perf_counter()

        with self.driver.session() as session:
            # Nodes, batched via UNWIND
            batch = []
            with open(nodes_path) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    batch.append({"id": row["id:ID"], "label": row["label"]})
                    if len(batch) >= BATCH_SIZE:
                        session.run(
                            "UNWIND $rows AS row "
                            "CREATE (n:Person {id: row.id})",
                            rows=batch,
                        )
                        node_count += len(batch)
                        batch = []
                if batch:
                    session.run(
                        "UNWIND $rows AS row CREATE (n:Person {id: row.id})",
                        rows=batch,
                    )
                    node_count += len(batch)
                    # Create index before relationship loading
            print("Creating Person.id index before loading relationships...")
            session.run(
             "CREATE INDEX person_id IF NOT EXISTS FOR (n:Person) ON (n.id)"
            ).consume()

                    

            # Edges, batched via UNWIND, matched by id property
            

            
            batch = []
            with open(edges_path) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    batch.append({"a": row[":START_ID"], "b": row[":END_ID"]})
                    if len(batch) >= BATCH_SIZE:
                        session.run(
                            "UNWIND $rows AS row "
                            "MATCH (a:Person {id: row.a}), (b:Person {id: row.b}) "
                            "CREATE (a)-[:FRIEND]->(b)",
                            rows=batch,
                        )
                        rel_count += len(batch)
                        batch = []
                if batch:
                    session.run(
                        "UNWIND $rows AS row "
                        "MATCH (a:Person {id: row.a}), (b:Person {id: row.b}) "
                        "CREATE (a)-[:FRIEND]->(b)",
                        rows=batch,
                    )
                    rel_count += len(batch)

        total_seconds = time.perf_counter() - start
        return {
            "nodes_per_sec": round(node_count / total_seconds, 2) if total_seconds else 0,
            "rels_per_sec": round(rel_count / total_seconds, 2) if total_seconds else 0,
            "total_seconds": round(total_seconds, 2),
            "load_method": f"neo4j driver, UNWIND batches of {BATCH_SIZE}",
        }

    def create_indexes(self) -> list:
        with self.driver.session() as session:
            session.run("CREATE INDEX person_id IF NOT EXISTS FOR (n:Person) ON (n.id)")
        return ["Person.id"]

    def sample_node_ids(self, n: int) -> list:
        with self.driver.session() as session:
            result = session.run(
                "MATCH (p:Person) RETURN p.id AS id ORDER BY rand() LIMIT $n", n=n
            )
            return [r["id"] for r in result]

    def traverse(self, start_id, hops: int):
        query = (
            f"MATCH (start:Person {{id: $id}})"
            f"-[:FRIEND*{hops}..{hops}]-(end) "
            f"RETURN count(DISTINCT end) AS c"
        )
        with self.driver.session() as session:
            return session.run(query, id=start_id).single()

    def point_lookup(self, node_id):
        with self.driver.session() as session:
            return session.run(
                "MATCH (p:Person {id: $id}) RETURN p", id=node_id
            ).single()

    def filtered_lookup(self, value):
        with self.driver.session() as session:
            return session.run(
                "MATCH (p:Person {id: $id}) RETURN p", id=value
            ).single()

    def aggregate_count_by_type(self):
        with self.driver.session() as session:
            return session.run(
                "MATCH ()-[r:FRIEND]->() RETURN type(r) AS rel_type, count(*) AS c"
            ).data()

    def mixed_read(self, node_id):
        with self.driver.session() as session:
            session.run(
                "MATCH (p:Person {id: $id})-[:FRIEND]->(f) RETURN f LIMIT 10",
                id=node_id,
            ).consume()

    def mixed_write(self, node_id):
        with self.driver.session() as session:
            session.run(
                "MATCH (p:Person {id: $id}) SET p.last_touched = timestamp()",
                id=node_id,
            ).consume()

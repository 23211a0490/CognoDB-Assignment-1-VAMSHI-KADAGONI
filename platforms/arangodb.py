import csv
import os
import time

from arango import ArangoClient

from common.base_platform import BasePlatform

BATCH_SIZE = 1000


class ArangoDBPlatform(BasePlatform):
    name = "arangodb"

    def __init__(self):
        self.endpoint = os.environ.get("ARANGO_ENDPOINT")
        self.user = os.environ.get("ARANGO_USER", "root")
        self.password = os.environ.get("ARANGO_PASSWORD")
        self.db_name = os.environ.get("ARANGO_DB_NAME", "benchmark")
        if not self.endpoint or not self.password:
            raise RuntimeError("arangodb: missing ARANGO_ENDPOINT or ARANGO_PASSWORD in .env")
        self.client = None
        self.sys_db = None
        self.db = None

    def connect(self):
        self.client = ArangoClient(hosts=self.endpoint)
        self.sys_db = self.client.db("_system", username=self.user, password=self.password)
        if not self.sys_db.has_database(self.db_name):
            self.sys_db.create_database(self.db_name)
        self.db = self.client.db(self.db_name, username=self.user, password=self.password)
        if not self.db.has_collection("people"):
            self.db.create_collection("people")
        if not self.db.has_collection("friend"):
            self.db.create_collection("friend", edge=True)

    def close(self):
        pass  # python-arango uses plain HTTP sessions, nothing to close

    def clear(self):
        self.db.collection("friend").truncate()
        self.db.collection("people").truncate()

    def load(self, nodes_path: str, edges_path: str) -> dict:
        people = self.db.collection("people")
        friend = self.db.collection("friend")
        node_count = 0
        rel_count = 0
        start = time.perf_counter()

        with open(nodes_path) as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                batch.append({"_key": row["id:ID"], "label": row["label"]})
                if len(batch) >= BATCH_SIZE:
                    people.insert_many(batch)
                    node_count += len(batch)
                    batch = []
            if batch:
                people.insert_many(batch)
                node_count += len(batch)

        with open(edges_path) as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                batch.append({
                    "_from": f"people/{row[':START_ID']}",
                    "_to": f"people/{row[':END_ID']}",
                })
                if len(batch) >= BATCH_SIZE:
                    friend.insert_many(batch)
                    rel_count += len(batch)
                    batch = []
            if batch:
                friend.insert_many(batch)
                rel_count += len(batch)

        total_seconds = time.perf_counter() - start
        return {
            "nodes_per_sec": round(node_count / total_seconds, 2) if total_seconds else 0,
            "rels_per_sec": round(rel_count / total_seconds, 2) if total_seconds else 0,
            "total_seconds": round(total_seconds, 2),
            "load_method": f"python-arango insert_many batches of {BATCH_SIZE}",
        }

    def create_indexes(self) -> list:
        return ["people._key (built-in primary index)"]

    def sample_node_ids(self, n: int) -> list:
        cursor = self.db.aql.execute(
            "FOR p IN people SORT RAND() LIMIT @n RETURN p._key", bind_vars={"n": n}
        )
        return list(cursor)

    def traverse(self, start_id, hops: int):
        query = f"""
        WITH people
        FOR v IN {hops}..{hops} OUTBOUND @start friend
        RETURN v
        """

        cursor = self.db.aql.execute(
        query,
        bind_vars={"start": f"people/{start_id}"}
        )
        return list(cursor)

    def point_lookup(self, node_id):
        return self.db.collection("people").get(node_id)

    def filtered_lookup(self, value):
        cursor = self.db.aql.execute(
            "FOR p IN people FILTER p._key == @v RETURN p", bind_vars={"v": value}
        )
        return list(cursor)

    def aggregate_count_by_type(self):
        cursor = self.db.aql.execute(
            "FOR e IN friend COLLECT WITH COUNT INTO c RETURN {rel_type: 'FRIEND', c: c}"
        )
        return list(cursor)

    def mixed_read(self, node_id):
        query = """
        WITH people
        FOR v IN 1..1 OUTBOUND @start friend
        LIMIT 10
        RETURN v
        """

        cursor = self.db.aql.execute(
        query,
        bind_vars={"start": f"people/{node_id}"},
        )
        list(cursor)

    def mixed_write(self, node_id):
        self.db.collection("people").update({"_key": node_id, "last_touched": time.time()})

    def footprint(self) -> dict:
        try:
            stats = self.db.collection("people").statistics()
            return {"stored_data_size": stats.get("figures", "not observable"), "memory_usage": "see ArangoDB Oasis dashboard"}
        except Exception:
            return {"stored_data_size": "not observable", "memory_usage": "not observable"}

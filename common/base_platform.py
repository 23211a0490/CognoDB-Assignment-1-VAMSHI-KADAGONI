"""
Every platform adapter (platforms/*.py) implements this interface. Workloads
in workloads/*.py are written entirely against this interface, so the exact
same workload code runs unmodified against every platform -- only the
adapter's internal query syntax (Cypher / AQL / Gremlin) differs.
"""
from abc import ABC, abstractmethod


class BasePlatform(ABC):
    name: str = "base"

    @abstractmethod
    def connect(self):
        """Open a connection/driver. Raise clearly if credentials are missing."""

    @abstractmethod
    def close(self):
        """Close the connection/driver cleanly."""

    @abstractmethod
    def clear(self):
        """Wipe any existing data so loads are reproducible from empty."""

    @abstractmethod
    def load(self, nodes_path: str, edges_path: str) -> dict:
        """
        Bulk/batch-loads nodes.csv and edges.csv (see data/prepare_dataset.py
        for the schema). Must return:
            {"nodes_per_sec": float, "rels_per_sec": float,
             "total_seconds": float, "load_method": str}
        `load_method` should describe what was actually used (e.g. "driver
        batched UNWIND, batch_size=1000" or "bulk CSV import tool") -- this
        goes straight into the README per the assignment's requirement.
        """

    @abstractmethod
    def create_indexes(self) -> list:
        """
        Creates whatever index(es) the lookups workload will exercise.
        Returns the list of indexed properties (for README documentation).
        """

    @abstractmethod
    def sample_node_ids(self, n: int) -> list:
        """Returns n randomly chosen existing node IDs, for traversal/lookup start points."""

    @abstractmethod
    def traverse(self, start_id, hops: int):
        """Runs a hops-deep neighbor expansion from start_id. Return value unused by timer."""

    @abstractmethod
    def point_lookup(self, node_id):
        """Look up a single node by its primary ID (not the indexed property)."""

    @abstractmethod
    def filtered_lookup(self, value):
        """Look up nodes by the indexed property created in create_indexes()."""

    @abstractmethod
    def aggregate_count_by_type(self):
        """Runs a COUNT/GROUP BY over relationship type (or label)."""

    @abstractmethod
    def mixed_read(self, node_id):
        """A single read op used by the mixed read/write workload."""

    @abstractmethod
    def mixed_write(self, node_id):
        """A single small write op (e.g. property update) used by the mixed workload."""

    def footprint(self) -> dict:
        """
        Optional override: return whatever the platform's API/console exposes
        about stored data size / memory usage. Default: not observable.
        """
        return {"stored_data_size": "not observable", "memory_usage": "not observable"}

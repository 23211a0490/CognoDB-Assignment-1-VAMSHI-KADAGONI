import os
from common.bolt_cypher_platform import BoltCypherPlatform


class MemgraphPlatform(BoltCypherPlatform):
    def __init__(self):
        super().__init__(
            uri=os.environ.get("MEMGRAPH_URI"),
            user=os.environ.get("MEMGRAPH_USER", "memgraph"),
            password=os.environ.get("MEMGRAPH_PASSWORD"),
            name="memgraph",
        )

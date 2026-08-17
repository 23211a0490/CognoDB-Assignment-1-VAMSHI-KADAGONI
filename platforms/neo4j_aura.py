import os
from common.bolt_cypher_platform import BoltCypherPlatform


class Neo4jAuraPlatform(BoltCypherPlatform):
    def __init__(self):
        super().__init__(
            uri=os.environ.get("NEO4J_AURA_URI"),
            user=os.environ.get("NEO4J_AURA_USER", "neo4j"),
            password=os.environ.get("NEO4J_AURA_PASSWORD"),
            name="neo4j_aura",
        )

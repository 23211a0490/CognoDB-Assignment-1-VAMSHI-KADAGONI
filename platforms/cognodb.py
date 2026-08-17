import os
from common.bolt_cypher_platform import BoltCypherPlatform


class CognoDBPlatform(BoltCypherPlatform):
    def __init__(self):
        super().__init__(
            uri=os.environ.get("COGNODB_URI"),
            user=os.environ.get("COGNODB_USER", "cognodb"),
            password=os.environ.get("COGNODB_PASSWORD"),
            name="cognodb",
        )

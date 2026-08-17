import json
from pathlib import Path


RESULTS_DIR = Path("results")

FILES = {
    "CognoDB": "run_20260817T115630Z.json",
    "Neo4j AuraDB": "run_20260817T122122Z.json",
    "Memgraph Cloud": "run_20260817T155309Z.json",
    "ArangoDB Oasis": "run_20260817T172549Z.json",
}


combined = {}

for platform, filename in FILES.items():
    path = RESULTS_DIR / filename

    if not path.exists():
        print(f"ERROR: Missing {path}")
        continue

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    combined[platform] = data


output_path = RESULTS_DIR / "summary.json"

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(combined, f, indent=2)


print()
print(f"Combined {len(combined)} successful platform results.")
print(f"Wrote: {output_path}")
"""Run from any directory: python examples/load.py. No third-party dependencies."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
records = json.loads((root / "data/processed/clean/records.json").read_text(encoding="utf-8"))
provenance = json.loads((root / "data/processed/clean/provenance.json").read_text(encoding="utf-8"))
locations = {}
for row in provenance:
    locations.setdefault(row["record_id"], []).append(row)
assert len(records) == 3963 and sum(map(len, locations.values())) == 3966
print(f"Loaded {len(records)} records and {len(provenance)} source locations")
# Resolve any record to all its original PDF pages without printing personal fields.
first_sources = locations[records[0]["record_id"]]
print([(source["document_id"], source["page_number"]) for source in first_sources])

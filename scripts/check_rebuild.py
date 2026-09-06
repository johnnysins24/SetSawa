"""Re-extract the frozen PDFs and compare committed canonical data with a fresh build."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from setsawa.core import sha256, write_json

subprocess.run([sys.executable, "-X", "utf8", "-m", "setsawa.pipeline", "build", "--output", ".cache/rebuild"], cwd=ROOT, check=True)
original, rebuilt = ROOT / "data/processed", ROOT / ".cache/rebuild"
files = [original / "raw/pages.jsonl", original / "raw/rows.jsonl", original / "raw/documents.json"]
files.extend(sorted((original / "clean").glob("*.json")))
files.extend(sorted((original / "clean").glob("*.csv")))
files.append(original / "clean/transformations.jsonl")
results = []
for path in files:
    other = rebuilt / path.relative_to(original)
    if sha256(path) != sha256(other):
        raise SystemExit("Rebuild mismatch: " + path.relative_to(ROOT).as_posix())
    results.append({"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path)})
write_json(ROOT / ".cache/rebuild-result.json", {"status": "passed", "canonical_file_count": len(results), "files": results, "parquet_xlsx": "semantic equivalence checked by validate; Excel PDF coordinates use 1e-9 pt absolute tolerance"})
print(f"Reproducibility passed: {len(results)} canonical files have identical SHA-256 hashes")

from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import importlib.metadata
import json
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

from .core import FIELDS, ROOT, VERSION, clean_cells, contained, digest, read_json, read_jsonl, scoped_id, sha256, write_csv, write_json, write_jsonl


def import_pdfs(source):
    source = Path(source).resolve(strict=True)
    baseline = read_json(ROOT / "config/snapshot.json")
    files = sorted(source.rglob("*.pdf"))
    if len(files) != 77 or len({p.name for p in files}) != 77:
        raise ValueError("Expected 77 uniquely named PDFs")
    target = ROOT / "data/raw/pdfs"
    target.mkdir(parents=True, exist_ok=True)
    for file in files:
        if file.is_symlink() or not file.resolve().is_relative_to(source):
            raise ValueError("Symlink input is not accepted")
        expected = baseline["pdf_sha256"].get(file.name)
        if not expected or sha256(file) != expected:
            raise ValueError("Source PDF hash differs from reviewed snapshot: " + file.name)
        destination = contained(target, file.name)
        if destination.exists() and sha256(destination) != expected:
            raise ValueError("Existing raw PDF differs; do not overwrite it")
        if not destination.exists():
            shutil.copyfile(file, destination)
    print("Preserved 77 byte-identical PDFs")


def extract(output):
    from .sandbox import parse_pdf
    baseline = read_json(ROOT / "config/snapshot.json")
    documents, pages, rows = [], [], []
    actual = {p.name for p in (ROOT / "data/raw/pdfs").iterdir()}
    if actual != set(baseline["pdf_sha256"]):
        raise ValueError("Raw PDF file set differs from the snapshot")
    for filename, expected in baseline["pdf_sha256"].items():
        path = contained(ROOT / "data/raw/pdfs", filename)
        if sha256(path) != expected:
            raise ValueError("Raw PDF hash mismatch: " + filename)
        result = parse_pdf(path)
        document_id = "pdf_" + filename.split("_", 1)[0]
        doc = {"document_id": document_id, "filename": filename, "relative_path": "data/raw/pdfs/" + filename, "sha256": expected, "bytes": path.stat().st_size, "page_count": len(result["pages"]), "province_name_th": path.stem.split("_", 1)[1], "source_document_number": int(filename[:2]), "metadata": result["metadata"], "summary": result["summary"], "active_content_flags": result["active_content_flags"]}
        scores = [clean_cells(row["cells"])["score_adjustment_reported"] for row in result["rows"]]
        calculated = {"source_row_count": len(scores), "score_sum": sum(scores), "score_max": max(scores, default=0)}
        if calculated != doc["summary"]:
            raise ValueError("Extracted table does not match document summary: " + filename)
        documents.append(doc)
        pages.extend({"document_id": document_id, **page} for page in result["pages"])
        rows.extend({"source_row_id": f"{document_id}:p{row['page_number']}:r{row['data_row_on_page']}", "document_id": document_id, **row} for row in result["rows"])
        print(f"Extracted {document_id}: {len(scores)} rows", flush=True)
    write_json(output / "raw/documents.json", documents)
    write_jsonl(output / "raw/pages.jsonl", pages)
    write_jsonl(output / "raw/rows.jsonl", rows)
    write_json(output / "raw/extraction-toolchain.json", {"pipeline_version": VERSION, "processed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "python": ".".join(map(str, sys.version_info[:2])), "packages": {name: importlib.metadata.version(name) for name in ("pdfplumber", "pdfminer.six", "pypdf")}})


def tables(output):
    raw = read_jsonl(output / "raw/rows.jsonl")
    docs = {d["document_id"]: d for d in read_json(output / "raw/documents.json")}
    unique, provenance, transformations = {}, [], []
    for row in raw:
        record = clean_cells(row["cells"])
        doc = docs[row["document_id"]]
        if record["province_name_th"] != doc["province_name_th"]:
            raise ValueError("Row province differs from its source document")
        record.update({"province_id": scoped_id("province", record["province_name_th"]), "district_id": scoped_id("district", record["province_name_th"], record["district_name_th"]), "agency_location_id": scoped_id("agency", record["province_name_th"], record["district_name_th"], record["agency_name_th"])})
        unique[record["record_id"]] = record
        provenance.append({"source_row_id": row["source_row_id"], "record_id": record["record_id"], "source_ordinal": int(row["cells"][0]), "document_id": doc["document_id"], "pdf_sha256": doc["sha256"], "pdf_relative_path": doc["relative_path"], "page_number": row["page_number"], "data_row_on_page": row["data_row_on_page"], "bbox_x0": row["bbox"][0], "bbox_top": row["bbox"][1], "bbox_x1": row["bbox"][2], "bbox_bottom": row["bbox"][3]})
        for field, original in zip(FIELDS, row["cells"][1:], strict=True):
            normalized = record[field]
            if original != normalized:
                transformations.append({"source_row_id": row["source_row_id"], "field": field, "original": original, "cleaned": normalized, "rule": "parse_integer" if field == "score_adjustment_reported" else "unicode_nfc_and_whitespace"})
    records = sorted(unique.values(), key=lambda r: r["record_id"])
    provenance.sort(key=lambda r: r["source_ordinal"])
    groups = collections.defaultdict(list)
    for p in provenance:
        groups[p["record_id"]].append(p)
    duplicates = [{"record_id": rid, "representative_source_row_id": values[0]["source_row_id"], "duplicate_source_row_id": p["source_row_id"], "representative_source_ordinal": values[0]["source_ordinal"], "duplicate_source_ordinal": p["source_ordinal"], "rule": "all_nine_normalized_content_fields_equal"} for rid, values in sorted(groups.items()) if len(values) > 1 for p in values[1:]]
    provinces = []
    for doc in docs.values():
        selected = [r for r in records if r["province_name_th"] == doc["province_name_th"]]
        provinces.append({"province_id": scoped_id("province", doc["province_name_th"]), "province_name_th": doc["province_name_th"], "document_id": doc["document_id"], "source_document_number": doc["source_document_number"], "source_row_count": doc["summary"]["source_row_count"], "record_count": len(selected), "source_score_sum": doc["summary"]["score_sum"], "record_score_sum": sum(r["score_adjustment_reported"] for r in selected)})
    districts, agencies = {}, {}
    for r in records:
        districts.setdefault(r["district_id"], {"district_id": r["district_id"], "province_id": r["province_id"], "province_name_th": r["province_name_th"], "district_name_th": r["district_name_th"], "record_count": 0})["record_count"] += 1
        agencies.setdefault(r["agency_location_id"], {"agency_location_id": r["agency_location_id"], "province_id": r["province_id"], "district_id": r["district_id"], "province_name_th": r["province_name_th"], "district_name_th": r["district_name_th"], "agency_name_th": r["agency_name_th"], "record_count": 0})["record_count"] += 1
    return {"records": records, "provenance": provenance, "duplicates": duplicates, "provinces": provinces, "districts": sorted(districts.values(), key=lambda x: x["district_id"]), "agency_locations": sorted(agencies.values(), key=lambda x: x["agency_location_id"])}, transformations


def clean(output):
    import pyarrow as pa
    import pyarrow.parquet as pq
    result, transformations = tables(output)
    for name, rows in result.items():
        write_json(output / f"clean/{name}.json", rows)
        write_csv(output / f"clean/{name}.csv", rows)
        pq.write_table(pa.Table.from_pylist(rows), output / f"clean/{name}.parquet", compression="zstd")
    write_jsonl(output / "clean/transformations.jsonl", transformations)
    write_json(output / "dataset.json", {"name": "SetSawa", "version": VERSION, "schema_version": "1.0.0", "dataset_year_be": 2568, "dataset_year_ce": 2025, "source_basis": "provided province PDFs; these reference an earlier CSV not provided", "source_data_license": "unspecified", "attribution_status": "tribute wording deferred", "record_id_contract": "rec_ + SHA-256 of UTF-8, key-sorted compact JSON of the nine normalized content fields; see schemas/records.schema.json", "geography_contract": "source-label groups; not official geographic codes or verified entities", "record_count": len(result["records"]), "source_row_count": len(result["provenance"])})
    print("Cleaned 3,966 source rows into 3,963 records with full provenance")


def validate(output, workbook=True):
    import jsonschema
    import pyarrow.parquet as pq
    expected, transforms = tables(output)
    raw = read_jsonl(output / "raw/rows.jsonl")
    docs = read_json(output / "raw/documents.json")
    pages = read_jsonl(output / "raw/pages.jsonl")
    baseline = read_json(ROOT / "config/snapshot.json")
    checks = []

    def require(condition, label):
        if not condition:
            raise ValueError("Validation failed: " + label)
        checks.append(label)

    require(len(docs) == 77 and len(pages) == 149, "77 documents / 149 pages")
    require({d["filename"]: d["sha256"] for d in docs} == baseline["pdf_sha256"], "manifest matches reviewed source hashes")
    for d in docs:
        require(sha256(contained(ROOT, d["relative_path"])) == d["sha256"], "PDF hash " + d["document_id"])
        docrows = [r for r in raw if r["document_id"] == d["document_id"]]
        scores = [int(r["cells"][3]) for r in docrows]
        require(d["summary"] == {"source_row_count": len(scores), "score_sum": sum(scores), "score_max": max(scores, default=0)}, "document summary " + d["document_id"])
        docpages = [p for p in pages if p["document_id"] == d["document_id"]]
        require([p["page_number"] for p in docpages] == list(range(1, d["page_count"] + 1)), "page coverage " + d["document_id"])
    for name, rows in expected.items():
        actual = read_json(output / f"clean/{name}.json")
        require(actual == rows, name + " independently regenerated from raw rows")
        require(pq.read_table(output / f"clean/{name}.parquet").to_pylist() == rows, name + " Parquet equivalence")
        with (output / f"clean/{name}.csv").open(encoding="utf-8", newline="") as f:
            csvrows = list(csv.DictReader(f))
        require(csvrows == [{k: str(v) for k, v in r.items()} for r in rows], name + " CSV equivalence")
    require(read_jsonl(output / "clean/transformations.jsonl") == transforms, "transformation log completeness")
    records, provenance = expected["records"], expected["provenance"]
    require(len(raw) == 3966 and len(records) == 3963, "3,966 source rows / 3,963 records")
    require(len({r["source_row_id"] for r in raw}) == 3966, "unique source row locations")
    require([p["source_ordinal"] for p in provenance] == list(range(1, 3967)), "source ordinal coverage 1..3966")
    require(len(expected["duplicates"]) == 3, "exactly three duplicate collapses")
    require(sum(int(r["cells"][3]) for r in raw) == 148954, "raw score sum 148954")
    require(sum(r["score_adjustment_reported"] for r in records) == 148888, "clean score sum 148888")
    require(len({r["record_id"] for r in records}) == 3963, "unique record IDs")
    require(len({r["cells"][1] for r in raw}) == 3944, "masked ID collisions retained")
    require({p["province_name_th"] for p in expected["provinces"] if p["record_count"] == 0} == {"กรุงเทพมหานคร", "พังงา"}, "both explicit zero-record provinces")
    require(len(expected["districts"]) == 659 and len(expected["agency_locations"]) == 2030, "geographically scoped groups")
    validator = jsonschema.Draft202012Validator(read_json(ROOT / "schemas/records.schema.json"))
    for record in records:
        validator.validate(record)
    checks.append("all records satisfy JSON Schema")
    if workbook:
        from .workbook import verify_workbook
        verify_workbook(output / "reader/setsawa.xlsx", expected)
        checks.append("Excel equivalence, literal strings, tables, filters and frozen headers")
    result = {"snapshot_version": VERSION, "status": "passed", "check_count": len(checks), "checks": checks, "documents": len(docs), "pages": len(pages), "source_rows": len(raw), "records": len(records), "duplicate_collapses": 3, "source_score_sum": 148954, "record_score_sum": 148888, "source_claims_verified": False}
    write_json(output / "quality/validation.json", result)
    print(f"Validation passed: {len(checks)} checks")
    return result


def package(output):
    validate(output)
    report = ROOT / "reports/quality-report.html"
    if not report.is_file():
        raise ValueError("Reviewed HTML report missing")
    review = read_json(ROOT / "reports/release-verification.json")
    for relative, expected_hash in review["reviewed_hashes"].items():
        if sha256(contained(ROOT, relative)) != expected_hash:
            raise ValueError("Reviewed artifact changed; repeat the affected review: " + relative)
    # Explicit allowlist. Import directory, virtualenv, caches and credentials are excluded.
    files = []
    for folder in ("data/raw/pdfs", "schemas", "docs", "examples", "notebooks", "reports", "config", "scripts", "tests"):
        files.extend(p for p in (ROOT / folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    files.extend(p for p in output.rglob("*") if p.is_file() and p.name != "checksums.sha256")
    for name in ("README.md", "LICENSE", "DATA-LICENSE.md", "SECURITY.md", "AGENTS.md", "CHANGELOG.md", "pyproject.toml", "uv.lock"):
        files.append(ROOT / name)
    files.extend((ROOT / "setsawa").glob("*.py"))
    files = sorted(set(files))
    from .security import scan_files
    scan_files(files)
    manifest = "".join(f"{sha256(p)}  {p.relative_to(ROOT).as_posix()}\n" for p in files)
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    (dist / "checksums.sha256").write_text(manifest, encoding="utf-8", newline="\n")
    archive = dist / f"setsawa-v{VERSION}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for file in files:
            info = zipfile.ZipInfo(file.relative_to(ROOT).as_posix(), date_time=(2026, 9, 6, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, file.read_bytes())
        z.writestr("checksums.sha256", manifest)
    (dist / "release-checksums.sha256").write_text(f"{sha256(archive)}  {archive.name}\n{sha256(report)}  quality-report.html\n{sha256(output / 'reader/setsawa.xlsx')}  setsawa.xlsx\n{sha256(dist / 'checksums.sha256')}  checksums.sha256\n", encoding="utf-8", newline="\n")
    print("Packaged " + str(archive))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["import", "extract", "clean", "workbook", "validate", "package", "build"])
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", default="data/processed", help="Repository-relative output root; use .cache/rebuild for reproducibility checks")
    args = parser.parse_args()
    output = contained(ROOT, args.output)
    if output == ROOT or output.is_relative_to(ROOT / "data/raw") or not (output.is_relative_to(ROOT / "data/processed") or output.is_relative_to(ROOT / ".cache")):
        raise ValueError("Output must be under data/processed or .cache")
    if args.command == "import":
        if not args.source:
            parser.error("import requires --source")
        import_pdfs(args.source)
    else:
        from .workbook import make_workbook
        actions = {"extract": lambda: extract(output), "clean": lambda: clean(output), "workbook": lambda: make_workbook(output), "validate": lambda: validate(output), "package": lambda: package(output)}
        if args.command == "build":
            for name in ("extract", "clean", "workbook", "validate"):
                actions[name]()
        else:
            actions[args.command]()


if __name__ == "__main__":
    main()

"""Rebuild the canonical technical report input and inspection notebook."""
import collections
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from setsawa.core import NOTICE, NOTICE_TH, read_json, read_jsonl, write_json

data = ROOT / "data/processed"
records = read_json(data / "clean/records.json")
provinces = read_json(data / "clean/provinces.json")
validation = read_json(data / "quality/validation.json")
source_notes = [{"document_id": p["document_id"], "page_number": 1, "note": line} for p in read_jsonl(data / "raw/pages.jsonl") if p["page_number"] == 1 for line in p["text"].splitlines() if line.startswith("หมายเหตุ")]
write_json(ROOT / "reports/source-geography-notes.json", source_notes)
source = {"id": "snapshot", "label": "SetSawa v1.0.0: 77 provided PDFs and validated transcription", "path": "data/processed/quality/validation.json", "query": {"engine": "Python", "language": "python", "description": "Transcribe all provided PDF tables, normalize nine content fields, deduplicate only complete matching content, and reconcile every document summary. Scope geography by province and district.", "tables_used": ["data/processed/clean/records.json", "data/processed/clean/provenance.json", "data/processed/clean/provinces.json", "data/processed/raw/documents.json"], "filters": ["All 77 documents; no source-row exclusions. Three duplicate extra occurrences mapped to existing content records."], "metric_definitions": {"record_count": "Count distinct content hashes across the nine normalized source fields, excluding only source ordinal.", "source_row_count": "Count every original table row including duplicate occurrences."}}}
title = "SetSawa data quality — 2568 / 2025"
blocks = [
    {"id": "title", "type": "markdown", "body": "# " + title},
    {"id": "summary", "type": "markdown", "sourceId": "snapshot", "body": "## All 3,966 source rows remain traceable\n\nThe 77 supplied PDFs contain 149 pages and yield **3,963 distinct content records** after three exact duplicate collapses. Every document's extracted row count, reported score sum and maximum reconcile with its printed summary. The clean dataset is suitable for source-linked retrieval and descriptive analysis of this collection.\n\n" + NOTICE + "\n\n" + NOTICE_TH},
    {"id": "definitions", "type": "markdown", "sourceId": "snapshot", "body": "## Count records and source rows separately\n\nA source row is one table occurrence, including its original sequence number. A clean record is the nine normalized content fields excluding that sequence number. Counts below describe this one supplied snapshot, not the population of candidates or confirmed cases. The label 2568 BE / 2025 CE is the collection year; PDF creation and processing dates are separate. Reported adjustments are integer source claims, not verified examination results."},
    {"id": "evidence", "type": "markdown", "sourceId": "snapshot", "body": "## Three duplicate pairs explain the count difference\n\nThe matching rule requires all nine fields to agree. The pairs occur in เพชรบูรณ์ (ordinals 3620/3621), ราชบุรี (550/551) and สุพรรณบุรี (956/957). Their reported adjustments are 30, 21 and 15. Keeping one occurrence per content record changes the reported sum from **148,954 to 148,888**. Both source locations remain available in provenance. No match is made solely from a name or masked identifier."},
    {"id": "geography", "type": "markdown", "sourceId": "snapshot", "body": "## Geography labels need their province context\n\n75 provinces contain records. Bangkok and Phang Nga have explicit empty documents. The 657 distinct district strings represent 659 province/district groups; 1,945 agency strings represent 2,030 province/district/agency groups. These are source-label groups, not verified entities. The chart compares the ten largest document groups by distinct content count. It does not measure geographic incidence or misconduct rates; no population denominator is supplied."},
    {"id": "chart", "type": "chart", "chartId": "province_counts", "layout": "full"},
    {"id": "province_table", "type": "table", "tableId": "province_detail", "layout": "full"},
    {"id": "method", "type": "markdown", "sourceId": "snapshot", "body": "## Rebuild from the preserved PDF bytes\n\nThe offline pipeline checks each PDF hash, rejects active content, extracts digital text and table geometry, applies NFC and conservative whitespace normalization, parses reported adjustments as integers, and produces content-addressed records. Every altered cell is logged. Each PDF runs in a bounded process. Raw cells and source metadata remain available. CSV, JSON, Parquet and Excel are cross-checked; an independent full rebuild compares canonical byte hashes. Excel PDF coordinates alone allow a 1e-9-point absolute rounding tolerance."},
    {"id": "limits", "type": "markdown", "sourceId": "snapshot", "body": "## Source claims and identities remain unverified\n\n22 masked-ID values repeat among the source rows; 19 remain collisions between distinct clean records. They are unsuitable as unique keys. No identity enrichment or hidden-digit reconstruction is performed. The PDFs refer to an earlier CSV that was not supplied. Website ingestion is deferred. There is no time series, authoritative entity registry, exam-participation denominator, or independent verification of allegations. Source-data licensing is unspecified. PDF checks and secret scans are defense in depth, not a guarantee against every exploit."},
    {"id": "next", "type": "markdown", "body": "## Use the versioned dataset before building the website\n\nConsumers should join records to provenance by record_id, group locations using scoped IDs, and preserve source qualifications in their interfaces. The next project phase is an accessible static Vercel site with source-page links, browser-side filtering, download documentation, protected previews and verified security headers.\n\n### Further questions\n\nAn original CSV, explicit source reuse terms, authoritative geography mappings and evidence of source authenticity would support future improvements. None is inferred in this release."},
]
artifact = {"surface": "report", "manifest": {"version": 1, "surface": "report", "title": title, "description": "Technical audit of the supplied source documents and reproducible clean data.", "generatedAt": "2026-09-06T00:00:00Z", "sources": [source], "blocks": blocks, "charts": [{"id": "province_counts", "type": "bar", "title": "Distinct records by province — ten largest groups", "subtitle": "Counts describe this collection; geographic rates cannot be inferred.", "dataset": "top_provinces", "sourceId": "snapshot", "encodings": {"x": {"field": "province_name_th", "type": "nominal", "label": "Province"}, "y": {"field": "record_count", "type": "quantitative", "label": "Distinct records", "format": "number"}}, "layout": "full"}], "tables": [{"id": "province_detail", "title": "All 77 province documents", "dataset": "provinces", "sourceId": "snapshot", "defaultSort": {"field": "record_count", "direction": "desc"}, "columns": [{"field": "province_name_th", "label": "จังหวัด / Province", "type": "text"}, {"field": "source_row_count", "label": "Source rows", "format": "number"}, {"field": "record_count", "label": "Distinct records", "format": "number"}, {"field": "record_score_sum", "label": "Reported adjustment sum", "format": "number"}]}]}, "snapshot": {"version": 1, "status": "ready", "generatedAt": "2026-09-06T00:00:00Z", "datasets": {"provinces": provinces, "top_provinces": sorted(provinces, key=lambda p: (-p["record_count"], p["province_name_th"]))[:10]}}, "sources": [source]}
sql = """SELECT p.province_name_th, p.source_row_count,
COUNT(r.record_id) AS record_count,
COALESCE(SUM(r.score_adjustment_reported), 0) AS record_score_sum
FROM provided_province_manifest AS p
LEFT JOIN clean_records AS r ON r.province_name_th = p.province_name_th
GROUP BY p.province_name_th, p.source_row_count
ORDER BY record_count DESC, p.province_name_th"""
with sqlite3.connect(":memory:") as db:
    db.row_factory = sqlite3.Row
    db.execute("CREATE TABLE provided_province_manifest (province_name_th TEXT PRIMARY KEY, source_row_count INTEGER)")
    db.execute("CREATE TABLE clean_records (record_id TEXT PRIMARY KEY, province_name_th TEXT, score_adjustment_reported INTEGER)")
    db.executemany("INSERT INTO provided_province_manifest VALUES (?, ?)", [(p["province_name_th"], p["source_row_count"]) for p in provinces])
    db.executemany("INSERT INTO clean_records VALUES (?, ?, ?)", [(r["record_id"], r["province_name_th"], r["score_adjustment_reported"]) for r in records])
    sql_provinces = [dict(row) for row in db.execute(sql)]
assert sum(p["record_count"] for p in sql_provinces) == len(records)
geo_source = {"id": "geography", "label": "Province counts recomputed in SQLite from released JSON", "path": "scripts/generate_report.py", "query": {"engine": "SQLite", "language": "sql", "sql": sql, "description": "Load data/processed/clean/provinces.json as provided_province_manifest and data/processed/clean/records.json as clean_records, then left-join to retain empty documents. Chart uses the first ten query rows; the table includes all 77.", "tables_used": ["provided_province_manifest", "clean_records"], "metric_definitions": {"record_count": "Count distinct clean content records within each province label, including explicit zero-record documents.", "source_row_count": "Original row count from each provided document's reconciled summary.", "record_score_sum": "Sum of adjustments reported in distinct content records; not verified scores."}}}
artifact["manifest"]["sources"].append(geo_source)
artifact["sources"].append(geo_source)
artifact["manifest"]["charts"][0]["sourceId"] = "geography"
artifact["manifest"]["charts"][0]["settings"] = {"orientation": "horizontal"}
artifact["manifest"]["tables"][0]["sourceId"] = "geography"
artifact["snapshot"]["datasets"] = {"provinces": sql_provinces, "top_provinces": sql_provinces[:10]}
next(b for b in artifact["manifest"]["blocks"] if b["id"] == "geography")["body"] += "\n\nNine PDF footnotes report 19 rows with unresolved district alternatives caused by same-name agencies within a province. Those source labels and footnotes are retained; no district is guessed. Consult the source page before treating a district group as a resolved location."
write_json(ROOT / "reports/artifact.json", artifact)
write_json(ROOT / "reports/report-notes.json", {"audience": "technical", "required_structure": "Title; technical summary; findings; definitions placed before evidence; methods; limitations; next steps; further questions", "chart_contract": {"question": "How many distinct records are present in the ten largest province groups?", "family": "bar", "variant": "single series; zero baseline; descending counts", "rows": 10, "grain": "province-label group", "denominator": "provided collection only", "surface": "portable HTML native chart", "palette": "shared renderer single-series theme; no categorical meaning", "non_color": "province labels and count axis", "limitation": "not an incidence/rate comparison"}, "table_rationale": "All 77 province counts are supplied as an exact audit lookup, including the two empty documents.", "verification": validation["status"]})

cells = []
def cell(kind, text):
    obj = {"cell_type": kind, "metadata": {}, "source": text.splitlines(keepends=True)}
    if kind == "code":
        obj.update({"execution_count": None, "outputs": []})
    cells.append(obj)
cell("markdown", "# SetSawa inspection\n\nRead-only checks of the released snapshot. Extraction accuracy does not verify source claims or personal identity. Run from the repository root or notebooks folder.\n")
cell("code", "import json\nfrom pathlib import Path\nfrom collections import Counter\nroot = Path.cwd() if (Path.cwd() / 'data').exists() else Path.cwd().parent\nload = lambda name: json.loads((root / 'data/processed/clean' / (name + '.json')).read_text(encoding='utf-8'))\nrecords, provenance, provinces = load('records'), load('provenance'), load('provinces')\nassert (len(records), len(provenance), len(provinces)) == (3963, 3966, 77)\n{'records': len(records), 'source_rows': len(provenance), 'provinces': len(provinces)}\n")
cell("markdown", "## Duplicate accounting\n\nThe three additional occurrences remain in provenance. Do not deduplicate by masked identifier.\n")
cell("code", "links = Counter(row['record_id'] for row in provenance)\nassert sum(n - 1 for n in links.values()) == 3\nassert len(load('duplicates')) == 3\nassert sum(r['score_adjustment_reported'] for r in records) == 148888\nassert sum(p['source_score_sum'] for p in provinces) == 148954\n{'duplicate_extra_occurrences': sum(n - 1 for n in links.values()), 'distinct_masked_ids': len({r['masked_id'] for r in records})}\n")
cell("markdown", "## Geography and source coverage\n\nThese are source labels, not official entity IDs or population-adjusted rates.\n")
cell("code", "assert len(load('districts')) == 659\nassert len(load('agency_locations')) == 2030\nassert sum(p['record_count'] for p in provinces) == len(records)\n[p['province_name_th'] for p in provinces if p['record_count'] == 0]\n")
cell("markdown", "## Source locations\n\nInspect page references without printing personal fields by default.\n")
cell("code", "rid = records[0]['record_id']\n[{k: p[k] for k in ('document_id', 'page_number', 'data_row_on_page', 'source_ordinal')} for p in provenance if p['record_id'] == rid]\n")
write_json(ROOT / "notebooks/profile.ipynb", {"nbformat": 4, "nbformat_minor": 4, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.12"}}, "cells": cells})
print("Generated canonical report input and read-only inspection notebook")

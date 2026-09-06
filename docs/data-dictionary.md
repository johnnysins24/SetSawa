# Data dictionary and joins

The authoritative machine contract is [records.schema.json](../schemas/records.schema.json). [records.d.ts](../schemas/records.d.ts) is generated from the same definition by `scripts/generate_contract.py`.

All strings use Unicode NFC and conservative whitespace normalization. Raw strings remain in `raw/rows.jsonl`. No name splitting, transliteration, fuzzy matching, identity enrichment, abbreviation expansion, or geographic enrichment is performed.

| Field | Type | Meaning |
| --- | --- | --- |
| `record_id` | string | Content hash, not a person identifier |
| `masked_id` | string | Existing `DDDxxxxxxDDDD` source mask, including leading zeros |
| `full_name_th` | string | Source Thai name |
| `score_adjustment_reported` | integer | Adjustment claimed by the source; observed 1–78 in this snapshot |
| `agency_name_th` | string | Source agency label |
| `source_status_text` | string | First “สถานะ” column; source claim |
| `district_name_th` | string | Source district label |
| `province_name_th` | string | Source province label |
| `source_location_basis_text` | string | Source explanation of agency/location confirmation |
| `source_verification_status_text` | string | Final “สถานะ” column; source claim |
| `province_id` | string | Province-label group hash |
| `district_id` | string | Province/district-label group hash |
| `agency_location_id` | string | Province/district/agency-label group hash |

## IDs

Record IDs are `rec_` followed by the full SHA-256 digest of UTF-8 JSON containing only the nine source-content fields. JSON uses sorted object keys, compact separators, literal Unicode, and integer score values. Original sequence number and provenance do not participate. A change to source content changes the content ID; corrections must publish an explicit old/new mapping in a future release.

Group IDs use the same JSON encoding of an ordered array of labels. Prefixes are `province_`, `district_`, and `agency_`. The file-number prefix (`01` through `77`) is a document ordering number, **not a government province code**.

## Relationships

- `records.record_id` → `provenance.record_id`: one-to-many; every source row appears exactly once in provenance.
- `provenance.source_row_id`: unique document/page/data-row address. Data rows are one-based and exclude the header.
- `provenance.source_ordinal`: original numeric first column, unique 1–3966 in this snapshot.
- `provenance.document_id` → `raw/documents.json`: PDF hash, filename, source metadata, page count and printed summary.
- `provenance.bbox_*`: PDF points, x from left and vertical coordinates from top; locate the original table row.
- `records.province_id`, `district_id`, `agency_location_id` → corresponding clean lookup tables.
- `duplicates`: representative and additional source row addresses and ordinals, with the exact matching rule.

`source_row_count` counts all input rows; `record_count` counts distinct content records. Their corresponding score sums deliberately differ after duplicate removal. District and agency tables count distinct records only. No missing-value convention is inferred: this snapshot has no empty source cells; an unexpected empty field fails validation.

All six clean tables have JSON, CSV and Parquet representations. JSON arrays and CSV rows share deterministic ordering. Parquet is typed, compressed with Zstandard, and semantically equivalent. Excel's data tabs retain the same English headers on row 4 and data from row 5; row 3 supplies Thai descriptions. Read `Read me` before interpreting source statuses.

# Extraction, cleaning and reproducibility

## Source boundary

The input consists of 77 user-provided PDFs from the collection รวมมิตรท้องถิ่น 68. Preserve the exact bytes and record SHA-256 hashes in `config/snapshot.json` and the document manifest. PDF metadata is source metadata, not proof of origin or authenticity. The documents refer to an earlier CSV not provided here. No website ingestion is part of v1.

## Extraction

Every PDF is checked against the frozen snapshot before parsing. Each runs in a separate Python process with an allowlisted environment, no inherited credentials, a 90-second wall-time limit, a 1 GiB memory limit, a 10 MiB input limit, a 50-page limit and bounded output. POSIX also enforces CPU/file-size limits; Windows uses a Job Object. A Python audit hook blocks networking and subprocess creation. This is defense in depth, not an OS privilege sandbox against native-library exploits.

The parser inspects the reachable object graph and rejects active actions, embedded files, remote actions and encryption. It requires exactly one table per page with the expected ten-column header. It records full page text, original cell strings, table geometry and row bounding boxes. Digital text is extracted directly; no OCR or third-party AI service is used.

Every document's extracted row count, sum and maximum are compared with its printed summary before output is accepted. All 149 pages contain a consistent table, including the two empty-province documents.

## Cleaning and duplicate decisions

Normalize strings with NFC and whitespace collapse; parse the reported `+N` score into an integer. Original values are retained and every changed field is logged in `transformations.jsonl`. Do not expand agency abbreviations or rewrite Thai spelling.

Compare all nine content columns, excluding only original sequence number. Three duplicate pairs meet this rule:

| Province | PDF page | Original ordinals | Reported adjustment removed from distinct-record sum |
| --- | ---: | --- | ---: |
| เพชรบูรณ์ | 1 | 3620, 3621 | 30 |
| ราชบุรี | 2 | 550, 551 | 21 |
| สุพรรณบุรี | 3 | 956, 957 | 15 |

Each pair has one content record linked to two original rows. The representative is the lower original ordinal; both retain equal source status. No record is merged solely on name or masked ID. Source sum 148,954 minus 66 equals distinct-record sum 148,888.

## Geographic ambiguity

657 distinct district strings become 659 province/district groups. 1,945 agency strings become 2,030 province/district/agency groups. These distinctions prevent accidental name-only merges; they are not independently validated entity resolution. Aggregate counts describe this collection, not geographic incidence or corruption rates.

Nine document footnotes explicitly report 19 rows with unresolved district alternatives because agencies share a name within a province. Preserve those labels rather than guessing a district. The original notes remain in page text and are indexed in `reports/source-geography-notes.json`. A non-empty district field therefore does not necessarily mean a resolved district.

## Validation and reproducibility

`validate` regenerates clean tables from retained raw cells, checks the snapshot metrics, PDF hashes, schema, provenance, original ordinals, per-document totals and cross-format equivalence. CI separately re-extracts every original PDF and compares the resulting canonical files against committed outputs. This binds retained extraction to the documents rather than trusting editable JSON alone.

`scripts/check_rebuild.py` performs a second full extraction/build in `.cache/rebuild`, compares raw pages/rows and all clean CSV/JSON hashes, and checks Parquet/Excel semantics. HTML is a portable presentation of the canonical report input; its presentation renderer is documented separately. Workbook ZIP metadata is fixed, but semantic equivalence is the required cross-platform contract for XLSX/Parquet.

Visual review covers first-page headers and representative rows from all provinces, the three duplicate locations and multi-page document endpoints. The review scope and evidence hashes are recorded in `reports/visual-review.json`; visual sampling supplements full automated table checks.

## Limitations

Extraction fidelity is not source authentication. The source's status/verification text is retained as a claim. Masked identifiers collide. No time series, candidate population, exam-participation denominator, authoritative agency register, or underlying original CSV is supplied. No temporal trend, guilt determination, identity conclusion, or rate comparison is supported by these files alone.

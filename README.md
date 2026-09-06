# SetSawa

**77 supplied province PDFs → 3,966 source rows → 3,963 distinct records, with every source row traceable.**

ชุดข้อมูลนี้จัดทำขึ้นเพื่อรักษา จัดโครงสร้าง และช่วยให้สามารถตรวจสอบข้อมูลที่ปรากฏในเอกสารต้นทางได้สะดวกขึ้น

Reproducible, source-faithful transcription of the provided **รวมมิตรท้องถิ่น 68** document collection. The collection concerns year **2568 BE / 2025 CE**; PDF creation dates and processing dates are different metadata.

> These records transcribe claims in the supplied documents. Checking extraction accuracy does **not** verify those claims, establish wrongdoing, or prove a person's identity. The source's own confirmation/status wording is preserved as a source claim. Similar names and masked IDs must not be used to infer identity.

## Download or read

- [Version 1.0.0 download package](https://github.com/johnnysins24/SetSawa/releases/tag/v1.0.0): original PDFs, clean data, workbook, report, and checksums.
- [CSV](data/processed/clean/records.csv) · [JSON](data/processed/clean/records.json) · [Parquet](data/processed/clean/records.parquet)
- [Excel workbook](data/processed/reader/setsawa.xlsx): nine sheets, filters, Thai descriptions, stable English field names, source references.
- [HTML quality report](reports/quality-report.html): download and open locally; GitHub's file view does not execute HTML.
- [Thai guide](docs/README.th.md) · [Data dictionary and joins](docs/data-dictionary.md) · [Methodology](docs/methodology.md)

## Snapshot facts

| Measure | Count |
| --- | ---: |
| Provided PDFs / pages | 77 / 149 |
| Original source rows | 3,966 |
| Distinct content records | 3,963 |
| Exact duplicate pairs | 3 |
| Provinces with records / documented provinces | 75 / 77 |
| Province-scoped district labels | 659 |
| Province/district/agency label combinations | 2,030 |
| Reported score sum, source rows / distinct records | 148,954 / 148,888 |

Bangkok and Phang Nga have explicit zero-record documents. These are represented in the province table. Geographic combinations are source-label groups, **not** verified organizations or official administrative codes. Do not interpret group size as a misconduct rate: population or exam-participation denominators are not supplied.

## Use the data

Python (standard library):

```python
import json
from pathlib import Path
records = json.loads(Path("data/processed/clean/records.json").read_text(encoding="utf-8"))
assert len(records) == 3963
```

Node.js (no npm dependencies):

```javascript
import { readFile } from 'node:fs/promises';
const records = JSON.parse(await readFile('data/processed/clean/records.json', 'utf8'));
console.log(records.length); // 3963
```

Use `record_id` to join to `provenance`. **Do not join on `masked_id`**: 22 values repeat in the source rows, and 19 collisions remain between distinct clean records. Examples with source-page lookup are in [examples](examples/).

Download all release assets into one directory, then run `python scripts/verify_download.py <directory>` to check the release hashes and every archived file without extracting it. Obtain the checksum manifest from the trusted repository release; checksums are not digital signatures.

CSV is UTF-8 without BOM, uses LF line endings and stable English headers. JSON is a flat array; Parquet preserves integer types. Excel users should prefer the workbook or select UTF-8 when importing CSV. Records sort by `record_id`; Thai names are preserved without automatic spelling correction. Raw extraction is JSONL so original strings can be retained without spreadsheet interpretation.

## Rebuild

Install Python **3.12** and [uv](https://docs.astral.sh/uv/), then:

```sh
uv sync --locked
uv run --locked python -m setsawa.pipeline build
uv run --locked pytest -q
uv run --locked python scripts/check_rebuild.py
uv run --locked python scripts/generate_report.py
uv run --locked python -m setsawa.pipeline package
```

`build` extracts the checked-in PDFs, cleans them, creates the workbook and validates all tables. It does not access the source website. The commands `extract`, `clean`, `workbook`, `validate`, and `package` can also run separately. Use `--output .cache/rebuild` to build without overwriting the checked-in generated data.

The supplied import folder is preserved locally and ignored by Git. The public copy of the PDFs is `data/raw/pdfs/`. `import --source <directory>` accepts only the exact reviewed snapshot hashes. Changing source files requires a reviewed snapshot update, not editing checks until they pass.

The canonical report input is reproducible with `scripts/generate_report.py`; the included HTML was exported with the Data Analytics portable report renderer. Rebuilding this presentation requires that renderer (see [report build notes](docs/report-build.md)); reading the report or rebuilding all datasets and Excel requires no Codex tools. The repository includes the final portable HTML.

## What is included

| Layer | Contents |
| --- | --- |
| `data/raw/pdfs/` | Byte-identical supplied PDFs |
| `data/processed/raw/` | PDF metadata, full extracted page text and original table cells |
| `data/processed/clean/` | Records, provenance, duplicates, geography groups, transformation log |
| `data/processed/reader/` | Excel workbook |
| `data/processed/quality/` | Machine-readable validation results |
| `schemas/` | JSON Schema and generated TypeScript interface |
| `notebooks/` | Inspectable profiling notebook |
| `reports/` | HTML report, report input and release verification evidence |

## Source and reuse terms

Input: the user-provided **รวมมิตรท้องถิ่น 68** PDFs. Their headers refer to an earlier CSV that was not supplied. The reference website is https://260816-karemairodnare.vercel.app/; website ingestion is deferred because its robots rules block AI crawlers. No website data or source code is included as a claimed crawl.

Project-authored code is [MIT](LICENSE). Source-document and source-data reuse terms are [unspecified](DATA-LICENSE.md); the code license does not relicense those materials. Tribute wording is deferred. Technical provenance is retained regardless.

## Security and corrections

Read [SECURITY.md](SECURITY.md) for parser limits, threat boundaries, private vulnerability reporting, and release integrity. Submit factual corrections as a source-linked issue or pull request. Do not add unmasked identifiers or claims about identity. Corrections are reviewed, versioned and described in the changelog; original source documents are never silently edited.

The Vercel website is a subsequent phase. See [the website handoff](docs/website-handoff.md).

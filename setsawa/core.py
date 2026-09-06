from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.0.0"
FIELDS = [
    "masked_id", "full_name_th", "score_adjustment_reported", "agency_name_th",
    "source_status_text", "district_name_th", "province_name_th",
    "source_location_basis_text", "source_verification_status_text",
]
HEADERS_TH = ["ID", "ชื่อ-สกุล", "แก้ไขคะแนน", "หน่วยงาน", "สถานะ", "อำเภอ", "จังหวัด", "ยืนยันหน่วยงาน/พื้นที่", "สถานะ"]
NOTICE = "Records transcribe claims in the provided PDFs. Extraction checks do not verify those claims or establish wrongdoing. Existing masked IDs are not unique personal identifiers."
NOTICE_TH = "ข้อมูลถอดจากเอกสารที่ได้รับ การตรวจสอบการถอดข้อมูลไม่ได้ยืนยันข้อกล่าวอ้างหรือความผิดของบุคคล รหัสที่ปิดบังบางส่วนไม่ใช่ตัวระบุบุคคลที่ไม่ซ้ำ"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize(value):
    if not isinstance(value, str):
        raise ValueError("Source cells must be strings; missing cells require review")
    return unicodedata.normalize("NFC", re.sub(r"\s+", " ", value).strip())


def clean_cells(cells):
    if len(cells) != 10 or not re.fullmatch(r"[0-9]+", cells[0] or ""):
        raise ValueError("Expected ten cells and a numeric source ordinal")
    values = [normalize(c) for c in cells[1:]]
    if any(not v for v in values):
        raise ValueError("Empty source field requires review")
    if not re.fullmatch(r"[0-9]{3}x{6}[0-9]{4}", values[0]):
        raise ValueError("Unexpected ID mask; never infer hidden digits")
    if not re.fullmatch(r"\+?[0-9]+", values[2]):
        raise ValueError("Unexpected score adjustment")
    values[2] = int(values[2])
    record = dict(zip(FIELDS, values, strict=True))
    record = {"record_id": "rec_" + digest(record), **record}
    return record


def scoped_id(kind, *labels):
    return kind + "_" + digest(list(labels))


def contained(root, relative):
    root = Path(root).resolve()
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts or ":" in str(relative):
        raise ValueError("Absolute paths, traversal and drive/stream paths are forbidden")
    result = (root / relative).resolve()
    if not result.is_relative_to(root):
        raise ValueError("Path escapes the selected root")
    return result


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(canonical(row) + "\n")


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def csv_value(value):
    # Canonical CSV is never silently escaped. Suspicious strings require review;
    # original values remain available losslessly in JSON/JSONL and the PDFs.
    if isinstance(value, str) and re.match(r"^[\s\ufeff]*[=+@\-]", value):
        raise ValueError("Spreadsheet formula-like text requires review before CSV export")
    return value


def write_csv(path, rows):
    if not rows:
        raise ValueError("Cannot infer CSV schema from an empty table")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: csv_value(v) for k, v in row.items()})

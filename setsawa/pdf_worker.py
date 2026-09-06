"""One bounded parser process per PDF. No network, subprocesses or inherited credentials.

Python audit restrictions reduce accidental access. They are not an OS exploit
sandbox; hostile files must additionally run in an isolated, secret-free runner.
"""
import json
import os
import re
import sys
from pathlib import Path

import pdfplumber
from pypdf import PdfReader
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject

FLAGS = {"/JavaScript", "/JS", "/Launch", "/EmbeddedFiles", "/EmbeddedFile", "/OpenAction", "/AA", "/RichMedia", "/XFA", "/SubmitForm", "/ImportData", "/URI", "/GoToR"}


def check_objects(reader):
    seen, stack, visits = set(), [reader.trailer], 0
    while stack:
        obj = stack.pop()
        visits += 1
        if visits > 200000:
            raise ValueError("PDF object traversal limit exceeded")
        if isinstance(obj, IndirectObject):
            key = (obj.idnum, obj.generation)
            if key in seen:
                continue
            seen.add(key)
            obj = obj.get_object()
        if isinstance(obj, DictionaryObject):
            for key, value in obj.items():
                if str(key) in FLAGS or (key in ("/S", "/Type") and str(value) in FLAGS):
                    raise ValueError("Active content, external action or attachment requires review: " + str(key))
                stack.append(value)
        elif isinstance(obj, ArrayObject):
            stack.extend(obj)


def restricted(event, args):
    if event.startswith("socket.") or event in {"subprocess.Popen", "os.system", "os.exec", "os.posix_spawn"}:
        raise PermissionError("Network and process creation disabled in PDF worker")


def extract(path):
    if path.stat().st_size > 10 * 1024 * 1024 or path.read_bytes()[:5] != b"%PDF-":
        raise ValueError("Not an allowed PDF (signature or size)")
    reader = PdfReader(path, strict=True)
    if reader.is_encrypted:
        raise ValueError("Encrypted PDF requires review")
    check_objects(reader)
    if not 1 <= len(reader.pages) <= 50:
        raise ValueError("Page limit exceeded")
    pages, rows, summary = [], [], None
    expected_header = ["ลำดับ", "ID", "ชื่อ-สกุล", "แก้ไขคะแนน", "หน่วยงาน", "สถานะ", "อำเภอ", "จังหวัด", "ยืนยันหน่วยงาน/พื้นที่", "สถานะ"]
    with pdfplumber.open(path) as pdf:
        for number, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            if not text or len(text) > 2_000_000:
                raise ValueError("Empty or oversized text page requires review")
            if number == 1:
                match = re.search(r"ยืนยันแล้ว\s+([\d,]+)\s+รายการ\s+คะแนนเพิ่มรวม\s+\+([\d,]+)\s+สูงสุด\s+\+([\d,]+)", text)
                if not match:
                    raise ValueError("Document summary missing")
                summary = dict(zip(["source_row_count", "score_sum", "score_max"], [int(x.replace(",", "")) for x in match.groups()]))
            tables = page.find_tables()
            if len(tables) != 1:
                raise ValueError("Expected exactly one table per page")
            table = tables[0]
            cells = table.extract()
            if cells[0] != expected_header:
                raise ValueError("Unexpected table header")
            pages.append({"page_number": number, "width_pt": page.width, "height_pt": page.height, "text": text, "table_header": cells[0], "table_bbox": list(table.bbox)})
            for row_number, row in enumerate(cells[1:], 1):
                if not any(row):
                    continue
                if len(row) != 10 or not re.fullmatch(r"[0-9]+", row[0] or ""):
                    raise ValueError("Unexpected table row")
                rows.append({"page_number": number, "data_row_on_page": row_number, "bbox": list(table.rows[row_number].bbox), "cells": row})
            page.close()
    return {"metadata": {str(k): str(v) for k, v in (reader.metadata or {}).items()}, "pages": pages, "rows": rows, "summary": summary, "active_content_flags": []}


if __name__ == "__main__":
    if sys.stdin.readline() != "GO\n":
        raise SystemExit("Worker requires bounded launcher")
    if os.name != "nt":
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
        resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
        resource.setrlimit(resource.RLIMIT_FSIZE, (32 * 1024**2, 32 * 1024**2))
    sys.addaudithook(restricted)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        print(json.dumps(extract(Path(sys.argv[1])), ensure_ascii=False, allow_nan=False))
    except Exception as error:
        print(type(error).__name__ + ": " + str(error), file=sys.stderr)
        sys.exit(1)

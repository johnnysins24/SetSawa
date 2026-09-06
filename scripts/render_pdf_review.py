"""Optional visual sampling. Requires Poppler's pdftoppm on PATH and Pillow.

Run only on the already validated snapshot. Output is local QA evidence, not a
replacement for PDF text/table reconciliation or an automated visual verdict.
"""
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from setsawa.core import read_json, contained, sha256

out = ROOT / ".cache/pdf-review"
out.mkdir(parents=True, exist_ok=True)
docs = read_json(ROOT / "data/processed/raw/documents.json")
tiles = []
for doc in docs:
    path = contained(ROOT, doc["relative_path"])
    if sha256(path) != doc["sha256"]:
        raise ValueError("Source hash mismatch")
    prefix = out / doc["document_id"]
    subprocess.run(["pdftoppm", "-f", "1", "-singlefile", "-scale-to", "1800", "-png", str(path), str(prefix)], check=True, timeout=60, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    with Image.open(str(prefix) + ".png") as image:
        tile = image.crop((0, 25, 1800, 235)).convert("RGB")
        ImageDraw.Draw(tile).text((5, 5), doc["document_id"], fill="black")
        tiles.append(tile)
for offset in range(0, len(tiles), 7):
    selected = tiles[offset:offset + 7]
    sheet = Image.new("RGB", (1800, 210 * len(selected)), "white")
    for index, tile in enumerate(selected):
        sheet.paste(tile, (0, index * 210))
    sheet.save(out / f"contact-{offset // 7 + 1:02}.png")
for number, page in [(54, 1), (55, 2), (57, 3), (3, 5), (67, 7)]:
    doc = docs[number - 1]
    subprocess.run(["pdftoppm", "-f", str(page), "-singlefile", "-scale-to", "2200", "-png", str(contained(ROOT, doc["relative_path"])), str(out / f"detail-{number}-{page}")], check=True, timeout=60, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
print("Rendered 77 first-page samples, three duplicate pages and two multi-page endpoints")

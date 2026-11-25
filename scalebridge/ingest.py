"""Ingest published CAG report PDFs into page-level text and retrieval chunks.

Every chunk keeps (report_id, file, page) so every answer can cite its source.
Public reports only. Originals are never modified.
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
TEXT = ROOT / "data" / "text"
INDEX = ROOT / "data" / "index"


@dataclass
class Chunk:
    chunk_id: str
    report_id: str
    report_title: str
    file: str
    page: int
    text: str


def pdf_pages(pdf: Path) -> list[str]:
    """Return one string per page using pdftotext (layout-free, form-feed separated)."""
    out = subprocess.run(["pdftotext", "-enc", "UTF-8", str(pdf), "-"],
                         capture_output=True, text=True, check=False).stdout
    return out.split("\f")


def chunk_page(text: str, size: int = 220, overlap: int = 40) -> list[str]:
    """Split page text into ~size-word windows with overlap. Paragraph numbers stay attached."""
    words = re.sub(r"[ \t]+", " ", text).split()
    if not words:
        return []
    chunks, step = [], max(1, size - overlap)
    for start in range(0, len(words), step):
        piece = " ".join(words[start:start + size])
        if len(piece) > 80:
            chunks.append(piece)
        if start + size >= len(words):
            break
    return chunks


def build(manifest_path: Path = ROOT / "data" / "manifest.json") -> list[Chunk]:
    """Read the manifest of downloaded reports and emit chunks.jsonl."""
    manifest = json.loads(manifest_path.read_text())
    TEXT.mkdir(parents=True, exist_ok=True)
    INDEX.mkdir(parents=True, exist_ok=True)
    chunks: list[Chunk] = []
    scanned_like = []
    import hashlib
    for rep in manifest:
        seen_pages: set[str] = set()  # full-report PDFs and chapter PDFs repeat the same pages
        for f in sorted(rep["files"], key=lambda x: -(RAW / x).stat().st_size if (RAW / x).exists() else 0):
            pdf = RAW / f
            if not pdf.exists():
                continue
            pages = pdf_pages(pdf)
            chars = sum(len(p.strip()) for p in pages)
            if pages and chars / max(1, len(pages)) < 200:
                scanned_like.append(f)  # likely scanned/image PDF: needs OCR, flagged not guessed
            (TEXT / (Path(f).stem + ".txt")).write_text("\f".join(pages))
            for pno, ptxt in enumerate(pages, start=1):
                key = hashlib.md5(" ".join(ptxt.split()).encode()).hexdigest()
                if len(ptxt.strip()) < 80 or key in seen_pages:
                    continue
                seen_pages.add(key)
                for i, piece in enumerate(chunk_page(ptxt)):
                    chunks.append(Chunk(f"{Path(f).stem}-p{pno}-{i}", rep["id"], rep["title"], f, pno, piece))
    with (INDEX / "chunks.jsonl").open("w") as fh:
        for c in chunks:
            fh.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")
    if scanned_like:
        (INDEX / "needs_ocr.json").write_text(json.dumps(scanned_like, indent=1))
    print(f"{len(chunks)} chunks from {len(manifest)} reports; {len(scanned_like)} files look scanned (see needs_ocr.json)")
    return chunks


if __name__ == "__main__":
    build()

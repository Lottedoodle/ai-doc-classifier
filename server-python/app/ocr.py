"""Extract plain text from uploaded documents (PDF text layer or Tesseract OCR)."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from pypdf import PdfReader


def extract_text_from_file(file_path: Path, mime_type: str) -> str:
    if mime_type == "application/pdf":
        return _extract_pdf_text(file_path)
    return _ocr_image(file_path)


def _extract_pdf_text(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)


def _find_tesseract() -> str | None:
    found = shutil.which("tesseract")
    if found:
        return found
    for candidate in (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ):
        if os.path.isfile(candidate):
            return candidate
    return None


def _ocr_image(file_path: Path) -> str:
    tesseract = _find_tesseract()
    if not tesseract:
        raise RuntimeError(
            "tesseract not found: install Tesseract OCR with Thai language pack (tha+eng)"
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        tmp_base = tmp.name[:-4]

    try:
        args = [tesseract, str(file_path), tmp_base, "-l", "tha+eng", "--psm", "3"]
        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "tesseract failed")
        return Path(f"{tmp_base}.txt").read_text(encoding="utf-8", errors="replace")
    finally:
        for path in (f"{tmp_base}.txt", tmp_base):
            try:
                os.unlink(path)
            except OSError:
                pass

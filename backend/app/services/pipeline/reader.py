from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.services.pipeline.errors import PipelineError

MIN_CHARS_PER_PAGE = 50          # en dessous : on considère le PDF comme un scan
MAX_PAGES = 100
MAX_VISION_BYTES = 18 * 1024 * 1024  # marge sous la limite de 32 Mo de l'API (base64 alourdit de 33 %)


@dataclass
class ReadResult:
    mode: str                    # "text" (texte natif) ou "vision" (le modèle lit l'image)
    text: str
    pages: int
    data: Optional[bytes] = None
    mime: Optional[str] = None


def _pdf_text(path: Path):
    import pdfplumber
    try:
        with pdfplumber.open(path) as pdf:
            n = len(pdf.pages)
            if n > MAX_PAGES:
                raise PipelineError(f"Document trop long ({n} pages, maximum {MAX_PAGES})")
            parts, chars = [], 0
            for i, page in enumerate(pdf.pages, 1):
                t = page.extract_text() or ""
                chars += len(t.strip())
                parts.append(f"--- Page {i} ---\n{t}")
            return n, chars, "\n".join(parts)
    except PipelineError:
        raise
    except Exception:
        raise PipelineError("PDF illisible ou protégé")


def _vision(path: Path, mime: str, pages: int) -> ReadResult:
    if path.stat().st_size > MAX_VISION_BYTES:
        raise PipelineError("Fichier trop volumineux pour l'analyse visuelle")
    return ReadResult(mode="vision", text="", pages=pages, data=path.read_bytes(), mime=mime)


def read_document(path: Path, mime: str) -> ReadResult:
    if mime == "application/pdf":
        pages, chars, text = _pdf_text(path)
        if chars >= MIN_CHARS_PER_PAGE * max(pages, 1):
            return ReadResult(mode="text", text=text, pages=pages)
        return _vision(path, mime, pages)  # PDF scanné
    return _vision(path, mime, 1)           # image
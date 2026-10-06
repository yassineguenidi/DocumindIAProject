import io
from pathlib import Path

from fastapi import HTTPException, status

from app.models import Document
from app.services.storage_service import storage

MAX_PAGES = 30
RENDER_SCALE = 1.6  # environ 115 dpi : lisible sans être lourd


def _path(doc: Document) -> Path:
    path = storage.open_path(doc.storage_key)
    if not path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fichier introuvable sur le serveur")
    return path


def get_layout(doc: Document) -> dict:
    """Pages et position de chaque mot (coordonnées normalisées entre 0 et 1)."""
    path = _path(doc)
    try:
        if doc.mime_type == "application/pdf":
            import pdfplumber

            pages = []
            with pdfplumber.open(path) as pdf:
                for i, page in enumerate(pdf.pages[:MAX_PAGES], 1):
                    w, h = float(page.width), float(page.height)
                    words = [
                        {
                            "t": wd["text"],
                            "x": round(wd["x0"] / w, 5),
                            "y": round(wd["top"] / h, 5),
                            "w": round((wd["x1"] - wd["x0"]) / w, 5),
                            "h": round((wd["bottom"] - wd["top"]) / h, 5),
                        }
                        for wd in page.extract_words()
                    ]
                    pages.append({"number": i, "width": w, "height": h, "words": words})
            return {"kind": "pdf", "pages": pages}

        from PIL import Image

        with Image.open(path) as im:
            width, height = im.size
        return {"kind": "image", "pages": [{"number": 1, "width": width, "height": height, "words": []}]}
    except Exception:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Document illisible")


def render_page(doc: Document, number: int):
    """Retourne (octets de l'image, type MIME) de la page demandée."""
    path = _path(doc)
    if doc.mime_type != "application/pdf":
        if number != 1:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Page introuvable")
        return path.read_bytes(), doc.mime_type

    import pypdfium2 as pdfium

    try:
        pdf = pdfium.PdfDocument(str(path))
    except Exception:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Document illisible")
    try:
        if not 1 <= number <= min(len(pdf), MAX_PAGES):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Page introuvable")
        buf = io.BytesIO()
        pdf[number - 1].render(scale=RENDER_SCALE).to_pil().save(buf, format="PNG")
        return buf.getvalue(), "image/png"
    finally:
        pdf.close()
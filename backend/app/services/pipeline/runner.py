import logging
import time

from app.db import SessionLocal
from app.models import Document, DocumentStatus
from app.services.pipeline import classifier, extractor, reader
from app.services.pipeline.errors import PipelineError
from app.services.pipeline.registry import REGISTRY
from app.services.storage_service import storage
from app.services import cross_checks
from app.services.candidates import index

log = logging.getLogger(__name__)


def _set_status(db, doc, status):
    doc.status = status
    db.commit()


def process_document(doc_id: int) -> None:
    """Exécuté en arrière-plan, avec sa propre session de base de données."""
    db = SessionLocal()
    try:
        doc = db.get(Document, doc_id)
        if doc is None:
            return
        started = time.monotonic()
        try:
            _set_status(db, doc, DocumentStatus.OCR)  # « Lecture » dans l'interface
            read = reader.read_document(storage.open_path(doc.storage_key), doc.mime_type)
            if read.mode == "text":
                doc.ocr_text = read.text
            doc_type, cls = classifier.classify(read)
            doc.doc_type = doc_type

            _set_status(db, doc, DocumentStatus.EXTRACTION)
            defn = REGISTRY.get(doc_type)
            if defn is None:
                data = {"_note": f"Extraction pas encore disponible pour le type « {doc_type} »"}
                meta = {"mode": read.mode, "pages": read.pages, "models": [], "escalated": False,
                        "input_tokens": 0, "output_tokens": 0}
            else:
                                
                ext = extractor.extract(defn, read)
                data, meta = ext.data, ext.meta
                issues = ext.issues + cross_checks.run(db, doc, data, doc_type)
                data["_validation"] = {
                    "ok": not issues,
                    "issues": [i["message"] for i in issues],
                    "details": issues,
                }

            _set_status(db, doc, DocumentStatus.VALIDATION)
            if cls is not None:  # coût de la classification par IA
                meta["input_tokens"] += cls.input_tokens
                meta["output_tokens"] += cls.output_tokens
            meta["seconds"] = round(time.monotonic() - started, 1)
            data["_meta"] = meta
            doc.extracted_data = data
            doc.error_message = None
            _set_status(db, doc, DocumentStatus.DONE)
            if doc_type == "cv":  # un échec d'indexation ne doit jamais faire échouer le document
                try:
                    index.index_candidate(db, doc)
                except Exception:
                    log.exception("Indexation du candidat impossible (document %s)", doc_id)
                    db.rollback()
        except Exception as exc:
            db.rollback()
            if not isinstance(exc, PipelineError):
                log.exception("Échec du traitement du document %s", doc_id)
            doc = db.get(Document, doc_id)
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(exc) if isinstance(exc, PipelineError) else "Erreur interne de traitement"
            db.commit()
    finally:
        db.close()
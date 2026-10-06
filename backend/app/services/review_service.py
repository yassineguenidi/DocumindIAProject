from datetime import datetime, timezone

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models import Document, DocumentStatus, User
from app.schemas.document import ReviewUpdate
from app.services.pipeline.registry import REGISTRY


def _fields_only(data: dict) -> dict:
    return {k: v for k, v in data.items() if not k.startswith("_") and k != "derived"}


def apply_review(db: Session, user: User, doc: Document, payload: ReviewUpdate) -> Document:
    if doc.status != DocumentStatus.DONE or not isinstance(doc.extracted_data, dict):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ce document n'est pas prêt pour la relecture")
    defn = REGISTRY.get(doc.doc_type or "")
    if defn is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ce type de document ne peut pas encore être relu")

    try:
        clean = defn.schema.model_validate(payload.data).model_dump()
    except ValidationError as exc:
        err = exc.errors()[0]
        where = ".".join(str(p) for p in err["loc"])
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Valeur invalide ({where}) : {err['msg']}")

    current = doc.extracted_data
    original = current.get("_ai_original") or _fields_only(current)  # la sortie de l'IA, conservée une fois pour toutes
    corrected = sorted(k for k in clean if clean.get(k) != original.get(k))
    issues = defn.validate(clean, doc.ocr_text or "")

    new = dict(clean)
    new["_meta"] = current.get("_meta", {})
    new["_ai_original"] = original
    new["_validation"] = {"ok": not issues, "issues": [i["message"] for i in issues], "details": issues}
    if defn.enrich:
        new["derived"] = defn.enrich(clean)
    new["_review"] = {
        "validated": payload.mark_validated,
        "validated_with_issues": payload.mark_validated and bool(issues),
        "by": user.id,
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "corrected_fields": corrected,
    }
    doc.extracted_data = new
    db.commit()
    db.refresh(doc)
    return doc
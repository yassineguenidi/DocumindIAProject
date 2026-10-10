import json
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models import Document, DocumentStatus, User
from app.services import export_service
from app.services.export_service import XLSX_MIME

router = APIRouter(prefix="/exports", tags=["exports"])


def _file(content, media_type: str, filename: str) -> Response:
    return Response(content, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{filename}"'})


def _json(obj, filename: str) -> Response:
    return _file(json.dumps(obj, ensure_ascii=False, indent=2, default=str), "application/json", filename)


@router.get("/invoices.xlsx")
def invoices_xlsx(date_from: Optional[date] = None, date_to: Optional[date] = None, validated_only: bool = False,
                  user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    content = export_service.invoices_workbook(db, user.company_id, date_from, date_to, validated_only)
    return _file(content, XLSX_MIME, f"factures-{date.today()}.xlsx")


@router.get("/invoices.json")
def invoices_json(date_from: Optional[date] = None, date_to: Optional[date] = None, validated_only: bool = False,
                  user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _json(export_service.invoices_json(db, user.company_id, date_from, date_to, validated_only), f"factures-{date.today()}.json")


@router.get("/candidates.xlsx")
def candidates_xlsx(anonymous: bool = False, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    suffix = "-anonymes" if anonymous else ""
    return _file(export_service.candidates_workbook(db, user.company_id, anonymous), XLSX_MIME, f"candidats{suffix}-{date.today()}.xlsx")


@router.get("/candidates.json")
def candidates_json(anonymous: bool = False, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    suffix = "-anonymes" if anonymous else ""
    return _json(export_service.candidates_json(db, user.company_id, anonymous), f"candidats{suffix}-{date.today()}.json")


@router.get("/documents/{doc_id}.json")
def document_json(doc_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.company_id == user.company_id).first()
    if not doc or doc.status != DocumentStatus.DONE or not isinstance(doc.extracted_data, dict):
        raise HTTPException(404, "Document introuvable")
    return _json(export_service.document_payload(doc), f"document-{doc.id}.json")
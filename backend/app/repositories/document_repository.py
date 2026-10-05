from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import Document, DocumentStatus
from sqlalchemy import func

def create(db: Session, **fields) -> Document:
    doc = Document(**fields)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_for_company(db: Session, doc_id: int, company_id: int) -> Optional[Document]:
    return (
        db.query(Document)
        .filter(Document.id == doc_id, Document.company_id == company_id)
        .first()
    )


IN_PROGRESS = [
    DocumentStatus.UPLOADING, DocumentStatus.QUEUED, DocumentStatus.OCR,
    DocumentStatus.EXTRACTION, DocumentStatus.VALIDATION,
]


def list_for_company(
    db: Session, company_id: int, skip: int, limit: int,
    q: Optional[str] = None, status: Optional[str] = None,
) -> Tuple[List[Document], int]:
    query = db.query(Document).filter(Document.company_id == company_id)
    if q:
        # on échappe % et _ pour qu'ils soient cherchés littéralement
        escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        query = query.filter(Document.original_filename.ilike(f"%{escaped}%", escape="\\"))
    if status == "in_progress":
        query = query.filter(Document.status.in_(IN_PROGRESS))
    elif status:
        query = query.filter(Document.status == DocumentStatus(status))
    total = query.count()
    items = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def count_since(db: Session, company_id: int, since: datetime) -> int:
    return (
        db.query(Document)
        .filter(
            Document.company_id == company_id,
            Document.created_at >= since,
            Document.status != DocumentStatus.FAILED,
        )
        .count()
    )


def delete(db: Session, doc: Document) -> None:
    db.delete(doc)
    db.commit()

def status_counts(db: Session, company_id: int) -> dict:
    rows = (
        db.query(Document.status, func.count(Document.id))
        .filter(Document.company_id == company_id)
        .group_by(Document.status)
        .all()
    )
    return {status.value: n for status, n in rows}


def created_dates_since(db: Session, company_id: int, since: datetime) -> List[datetime]:
    rows = (
        db.query(Document.created_at)
        .filter(Document.company_id == company_id, Document.created_at >= since)
        .all()
    )
    return [r[0] for r in rows]    
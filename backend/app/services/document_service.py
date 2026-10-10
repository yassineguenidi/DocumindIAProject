import os

from collections import Counter
from datetime import datetime, time, timedelta, timezone

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models import Document, DocumentStatus, User
from app.repositories import document_repository
from app.schemas.document import UsageResponse, StatsResponse, ActivityPoint
from app.services.storage_service import FileTooLarge, storage

from typing import BinaryIO

# extension -> (mime accepté, signature des premiers octets)
ALLOWED = {
    ".pdf": ("application/pdf", b"%PDF-"),
    ".png": ("image/png", b"\x89PNG\r\n\x1a\n"),
    ".jpg": ("image/jpeg", b"\xff\xd8\xff"),
    ".jpeg": ("image/jpeg", b"\xff\xd8\xff"),
}


def _month_start() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_usage(db: Session, user: User) -> UsageResponse:
    plan = user.company.plan
    used = document_repository.count_since(db, user.company_id, _month_start())
    quota = plan.monthly_doc_quota
    return UsageResponse(
        plan=plan.code,
        quota=quota,
        used=used,
        remaining=None if quota is None else max(quota - used, 0),
        period_start=_month_start(),
        max_file_size_mb=plan.max_file_size_mb,
    )


def get_stats(db: Session, user: User) -> StatsResponse:
    counts = document_repository.status_counts(db, user.company_id)
    total = sum(counts.values())
    done, failed = counts.get("done", 0), counts.get("failed", 0)

    days = 14
    start = datetime.now(timezone.utc).date() - timedelta(days=days - 1)
    since = datetime.combine(start, time.min, tzinfo=timezone.utc)
    per_day = Counter(d.date() for d in document_repository.created_dates_since(db, user.company_id, since))
    activity = [
        ActivityPoint(date=(start + timedelta(days=i)).isoformat(), count=per_day.get(start + timedelta(days=i), 0))
        for i in range(days)
    ]
    return StatsResponse(total=total, in_progress=total - done - failed, done=done, failed=failed, activity=activity)  

# def upload(db: Session, user: User, file: UploadFile) -> Document:
#     plan = user.company.plan

#     # 1. Quota
#     usage = get_usage(db, user)
#     if usage.remaining is not None and usage.remaining <= 0:
#         raise HTTPException(
#             status.HTTP_403_FORBIDDEN,
#             f"Quota mensuel atteint ({usage.quota} documents). Passez à un plan supérieur.",
#         )

#     # 2. Type de fichier : extension, type MIME et signature réelle
#     filename = os.path.basename(file.filename or "document")[:255]
#     ext = os.path.splitext(filename)[1].lower()
#     if ext not in ALLOWED:
#         raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Formats acceptés : PDF, PNG, JPG")
#     mime, signature = ALLOWED[ext]

#     head = file.file.read(len(signature))
#     file.file.seek(0)
#     if not head.startswith(signature):
#         raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Le contenu du fichier ne correspond pas à son extension")

#     # 3. Sauvegarde avec limite de taille du plan
#     max_bytes = plan.max_file_size_mb * 1024 * 1024
#     try:
#         key, size = storage.save(user.company_id, ext, file.file, max_bytes)
#     except FileTooLarge:
#         raise HTTPException(
#             status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
#             f"Fichier trop volumineux (max {plan.max_file_size_mb} Mo pour votre plan)",
#         )

#     # 4. Enregistrement en base
#     try:
#         return document_repository.create(
#             db,
#             company_id=user.company_id,
#             uploaded_by_id=user.id,
#             original_filename=filename,
#             storage_key=key,
#             mime_type=mime,
#             size_bytes=size,
#             status=DocumentStatus.QUEUED,
#         )
#     except Exception:
#         storage.delete(key)  # pas de fichier orphelin si la base échoue
#         raise

def ingest(db: Session, user: User, filename: str, stream: BinaryIO) -> Document:
    """Dépose un document (site ou email) : quota, type de fichier, signature, taille."""
    plan = user.company.plan

    usage = get_usage(db, user)
    if usage.remaining is not None and usage.remaining <= 0:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"Quota mensuel atteint ({usage.quota} documents). Passez à un plan supérieur.",
        )

    filename = os.path.basename(filename or "document")[:255]
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Formats acceptés : PDF, PNG, JPG")
    mime, signature = ALLOWED[ext]

    head = stream.read(len(signature))
    stream.seek(0)
    if not head.startswith(signature):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Le contenu du fichier ne correspond pas à son extension")

    max_bytes = plan.max_file_size_mb * 1024 * 1024
    try:
        key, size = storage.save(user.company_id, ext, stream, max_bytes)
    except FileTooLarge:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"Fichier trop volumineux (max {plan.max_file_size_mb} Mo pour votre plan)",
        )

    try:
        return document_repository.create(
            db,
            company_id=user.company_id,
            uploaded_by_id=user.id,
            original_filename=filename,
            storage_key=key,
            mime_type=mime,
            size_bytes=size,
            status=DocumentStatus.QUEUED,
        )
    except Exception:
        storage.delete(key)  # pas de fichier orphelin si la base échoue
        raise


def upload(db: Session, user: User, file: UploadFile) -> Document:
    return ingest(db, user, file.filename or "document", file.file)

def delete(db: Session, user: User, doc_id: int) -> None:
    doc = document_repository.get_for_company(db, doc_id, user.company_id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document introuvable")
    key = doc.storage_key
    document_repository.delete(db, doc)
    storage.delete(key)
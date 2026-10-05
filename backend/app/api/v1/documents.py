from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse

from app.services.storage_service import storage

from app.api.deps import get_current_user
from app.db import get_db
from app.models import User
from app.repositories import document_repository
from app.schemas.document import DocumentList, DocumentResponse, UsageResponse, StatsResponse
from app.services import document_service

from app.models import DocumentStatus, User
from app.services.pipeline.runner import process_document

router = APIRouter(prefix="/documents", tags=["documents"])


# @router.post("/upload", response_model=DocumentResponse, status_code=201)
# def upload(
#     file: UploadFile = File(...),
#     user: User = Depends(get_current_user),
#     db: Session = Depends(get_db),
# ):
#     return document_service.upload(db, user, file)

@router.post("/upload", response_model=DocumentResponse, status_code=201)
def upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = document_service.upload(db, user, file)
    background_tasks.add_task(process_document, doc.id)
    return doc


@router.post("/{doc_id}/reprocess", response_model=DocumentResponse)
def reprocess(
    doc_id: int,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = document_repository.get_for_company(db, doc_id, user.company_id)
    if not doc:
        raise HTTPException(404, "Document introuvable")
    if doc.status not in (DocumentStatus.FAILED, DocumentStatus.DONE):
        raise HTTPException(409, "Ce document est déjà en cours de traitement")
    doc.status = DocumentStatus.QUEUED
    doc.error_message = None
    db.commit()
    background_tasks.add_task(process_document, doc.id)
    return doc

@router.get("/usage", response_model=UsageResponse)
def usage(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return document_service.get_usage(db, user)

@router.get("/stats", response_model=StatsResponse)
def stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return document_service.get_stats(db, user)

@router.get("", response_model=DocumentList)
def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    q: Optional[str] = Query(None, max_length=100),
    status: Optional[str] = Query(
        None, pattern="^(in_progress|uploading|queued|ocr|extraction|validation|done|failed)$"
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = document_repository.list_for_company(db, user.company_id, skip, limit, q, status)
    return DocumentList(items=items, total=total) 


@router.get("/{doc_id}", response_model=DocumentResponse)
def get_document(doc_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = document_repository.get_for_company(db, doc_id, user.company_id)
    if not doc:
        raise HTTPException(404, "Document introuvable")
    return doc


@router.get("/{doc_id}/download")
def download_document(doc_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = document_repository.get_for_company(db, doc_id, user.company_id)
    if not doc:
        raise HTTPException(404, "Document introuvable")
    path = storage.open_path(doc.storage_key)
    if not path.exists():
        raise HTTPException(404, "Fichier introuvable sur le serveur")
    return FileResponse(path, media_type=doc.mime_type, filename=doc.original_filename)

@router.delete("/{doc_id}", status_code=204)
def delete_document(doc_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    document_service.delete(db, user, doc_id)
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models import CandidateProfile, Document, DocumentStatus, User
from app.schemas.candidate import JobTextRequest, MatchRequest
from app.services.candidates import anonymize, index, matching
from app.services.candidates import search as search_service
from app.services.candidates.export_docx import DOCX_MIME, build_docx
from app.services.pipeline.errors import PipelineError

router = APIRouter(prefix="/candidates", tags=["candidates"])


def _cv_doc(db: Session, user: User, doc_id: int):
    d = db.query(Document).filter(
        Document.id == doc_id, Document.company_id == user.company_id,
        Document.doc_type == "cv", Document.status == DocumentStatus.DONE,
    ).first()
    if not d or not isinstance(d.extracted_data, dict):
        raise HTTPException(404, "Candidat introuvable")
    p = db.query(CandidateProfile).filter(CandidateProfile.document_id == d.id).first()
    return d, p


def _view(d: Document, anonymous: bool) -> dict:
    data = {k: v for k, v in d.extracted_data.items() if not k.startswith("_") and k != "derived"}
    return anonymize.anonymize_cv(data, d.id) if anonymous else data


def _years(d: Document, p: Optional[CandidateProfile]) -> float:
    return float(p.years if p else (d.extracted_data.get("derived") or {}).get("total_experience_years") or 0)


@router.get("/search")
def search(
    q: str = Query("", max_length=300),
    min_years: Optional[float] = Query(None, ge=0),
    skills: List[str] = Query(default=[]),
    language: Optional[str] = Query(None, max_length=50),
    location: Optional[str] = Query(None, max_length=100),
    anonymous: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return search_service.search(db, user.company_id, q.strip(), min_years, [s for s in skills if s.strip()], language, location, anonymous)


@router.post("/reindex")
def reindex(background_tasks: BackgroundTasks, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    indexed = {r[0] for r in db.query(CandidateProfile.document_id).filter(CandidateProfile.company_id == user.company_id)}
    ids = [r[0] for r in db.query(Document.id).filter(
        Document.company_id == user.company_id, Document.doc_type == "cv", Document.status == DocumentStatus.DONE)
        if r[0] not in indexed]
    for doc_id in ids:
        background_tasks.add_task(index.reindex_candidate, doc_id)
    return {"queued": len(ids)}


@router.post("/job-criteria")
def job_criteria(data: JobTextRequest, user: User = Depends(get_current_user)):
    try:
        return matching.parse_job(data.text)
    except PipelineError as exc:
        raise HTTPException(502, str(exc))


@router.post("/match")
def match(data: MatchRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return matching.match(db, user.company_id, data.criteria, data.job_text, data.anonymous)


@router.get("/{doc_id}")
def detail(doc_id: int, anonymous: bool = False, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    d, p = _cv_doc(db, user, doc_id)
    return {
        "document_id": d.id,
        "name": anonymize.display_name(d.id, d.extracted_data, anonymous),
        "filename": None if anonymous else d.original_filename,  # un nom de fichier contient souvent le nom du candidat
        "years": _years(d, p),
        "job_family": p.job_family if p else None,
        "data": _view(d, anonymous),
        "skills": list(p.skills) if p else [s.get("name") for s in d.extracted_data.get("skills") or []],
        "inferred_skills": list(p.inferred_skills) if p else [],
    }


@router.get("/{doc_id}/export")
def export(doc_id: int, anonymous: bool = False, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    d, p = _cv_doc(db, user, doc_id)
    content = build_docx(_view(d, anonymous), anonymize.display_name(d.id, d.extracted_data, anonymous), user.company.name, _years(d, p))
    suffix = "-anonyme" if anonymous else ""
    return Response(content, media_type=DOCX_MIME, headers={"Content-Disposition": f'attachment; filename="dossier-candidat-{d.id}{suffix}.docx"'})
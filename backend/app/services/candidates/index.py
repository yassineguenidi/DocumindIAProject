import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import CandidateProfile, Document, DocumentStatus
from app.services.candidates import anonymize, embeddings, enrich, skills

log = logging.getLogger(__name__)


def _cv_input(data: dict, names: list) -> dict:
    """Le CV tel qu'envoyé au modèle : aucune identité, textes libres nettoyés."""
    return {
        "headline": data.get("headline"),
        "summary": anonymize.scrub_text(data.get("summary"), names),
        "experiences": [
            {
                "index": i, "title": e.get("title"), "company": e.get("company"),
                "start_date": e.get("start_date"), "end_date": e.get("end_date"),
                "description": anonymize.scrub_text(e.get("description"), names),
            }
            for i, e in enumerate(data.get("experiences") or [])
        ],
        "education": [{"degree": e.get("degree"), "field": e.get("field")} for e in data.get("education") or []],
        "declared_skills": [s.get("name") for s in data.get("skills") or []],
    }


def _search_text(data: dict, titles: list, declared: list, inferred: list, names: list) -> str:
    parts = [data.get("headline"), data.get("summary"), data.get("location"), " ".join(titles),
             ", ".join(declared), ", ".join(i["name"] for i in inferred)]
    for e in data.get("experiences") or []:
        parts += [e.get("title"), e.get("company"), e.get("description")]
    for e in data.get("education") or []:
        parts += [e.get("degree"), e.get("field")]
    parts += [c.get("name") for c in data.get("certifications") or []]
    parts += [l.get("language") for l in data.get("languages") or []]
    text = "\n".join(str(p) for p in parts if p)
    return (anonymize.scrub_text(text, names) or "")[:8000]


def index_candidate(db: Session, doc: Document) -> None:
    data = doc.extracted_data
    if not isinstance(data, dict) or doc.doc_type != "cv":
        return
    names = anonymize.name_parts(data)
    enr = enrich.enrich_cv(_cv_input(data, names)) or {}

    declared = list(dict.fromkeys(skills.canonical(s["name"]) for s in data.get("skills") or [] if s.get("name")))
    known = {skills.fold(s) for s in declared}
    inferred = []
    for it in enr.get("inferred_skills", []):
        canon = skills.canonical(it["name"])
        if skills.fold(canon) not in known:
            known.add(skills.fold(canon))
            inferred.append({"name": canon, "evidence": it["evidence"], "experience_index": it["experience_index"]})
    titles = [t["normalized_title"] for t in enr.get("titles", [])]

    text = _search_text(data, titles, declared, inferred, names)
    vectors = embeddings.embed([text], "doc")

    profile = db.query(CandidateProfile).filter(CandidateProfile.document_id == doc.id).first()
    if profile is None:
        profile = CandidateProfile(document_id=doc.id, company_id=doc.company_id)
        db.add(profile)
    profile.years = float((data.get("derived") or {}).get("total_experience_years") or 0)
    profile.job_family = enr.get("job_family")
    profile.titles, profile.skills, profile.inferred_skills = titles, declared, inferred
    profile.search_text = text
    profile.embedding = vectors[0] if vectors else None
    profile.embedding_model = embeddings.model_name() if vectors else None
    profile.updated_at = datetime.now(timezone.utc)
    db.commit()


def reindex_candidate(doc_id: int) -> None:
    """Tâche de fond : session propre, erreurs journalisées sans jamais bloquer l'utilisateur."""
    db = SessionLocal()
    try:
        doc = db.get(Document, doc_id)
        if doc and doc.status == DocumentStatus.DONE:
            index_candidate(db, doc)
    except Exception:
        log.exception("Indexation du candidat %s impossible", doc_id)
        db.rollback()
    finally:
        db.close()
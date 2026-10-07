import logging
from typing import List

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import CandidateProfile
from app.schemas.candidate import JobCriteria
from app.services.candidates import embeddings, search, skills
from app.services.pipeline import llm
from app.services.pipeline.reader import ReadResult

log = logging.getLogger(__name__)

TASK = (
    "Voici une offre d'emploi. Extrais les critères : title, must_have (compétences, outils ou qualifications indispensables, "
    "une par entrée, formulées de façon courte), nice_to_have (souhaités), min_years (expérience minimale demandée, nombre) et "
    "languages (langues exigées). Ne retiens que ce qui est écrit. N'inclus AUCUN critère d'âge, de genre, de nationalité, "
    "de situation familiale, d'état de santé ou d'apparence."
)


def parse_job(text: str) -> dict:
    doc = ReadResult(mode="text", text=text, pages=1)
    res = llm.call_tool(settings.LLM_MODEL_FAST, "extract_job_criteria", "Extrait les critères d'une offre", JobCriteria, doc, TASK, 1500)
    return JobCriteria.model_validate(res.data).model_dump()


def _skill_evidence(skill: str, data: dict, p: CandidateProfile):
    declared = {skills.fold(s) for s in p.skills or []}
    if any(a in declared for a in skills.aliases_of(skill)):
        return "met", "Compétence déclarée dans le CV"
    for e in data.get("experiences") or []:
        if skills.mentioned(skill, skills.fold(f"{e.get('title') or ''} {e.get('description') or ''}")):
            return "met", f"Mentionnée dans l'expérience « {e.get('title') or '?'} » chez {e.get('company') or '?'}"
    for c in data.get("certifications") or []:
        if skills.mentioned(skill, skills.fold(c.get("name") or "")):
            return "met", f"Certification : {c.get('name')}"
    for e in data.get("education") or []:
        if skills.mentioned(skill, skills.fold(f"{e.get('degree') or ''} {e.get('field') or ''}")):
            return "met", f"Formation : {e.get('degree') or e.get('field')}"
    for inf in p.inferred_skills or []:
        if skills.mentioned(skill, skills.fold(inf["name"])):
            return "to_confirm", f"Déduite par l'IA, à confirmer : {inf.get('evidence') or inf['name']}"
    return "missing", "Non trouvée dans le CV"


def evaluate(data: dict, p: CandidateProfile, c: JobCriteria) -> dict:
    results: List[dict] = []
    for kind, items in (("must", c.must_have), ("nice", c.nice_to_have)):
        for s in items:
            status, evidence = _skill_evidence(s, data, p)
            results.append({"kind": kind, "label": s, "status": status, "evidence": evidence})
    if c.min_years:
        ok = (p.years or 0) >= c.min_years
        results.append({"kind": "years", "label": f"{c.min_years:g} ans d'expérience minimum",
                        "status": "met" if ok else "missing", "evidence": f"{p.years:g} ans d'expérience (calculé à partir des dates)"})
    for lang in c.languages:
        found = next((l for l in data.get("languages") or [] if skills.fold(lang) in skills.fold(l.get("language") or "")), None)
        results.append({"kind": "language", "label": lang, "status": "met" if found else "missing",
                        "evidence": (f"{found['language']}" + (f" ({found['level']})" if found.get("level") else "")) if found else "Non indiquée dans le CV"})

    must = [r for r in results if r["kind"] in ("must", "years", "language")]
    nice = [r for r in results if r["kind"] == "nice"]
    return {
        "criteria": results,
        "summary": {
            "must_met": sum(r["status"] == "met" for r in must), "must_to_confirm": sum(r["status"] == "to_confirm" for r in must),
            "must_total": len(must), "nice_met": sum(r["status"] == "met" for r in nice), "nice_total": len(nice),
        },
    }


def match(db: Session, company_id: int, criteria: JobCriteria, job_text: str, anonymous: bool) -> List[dict]:
    rows = search.load_candidates(db, company_id)
    query = job_text.strip() or " ".join([criteria.title or "", *criteria.must_have, *criteria.nice_to_have])
    qv = embeddings.embed([query[:4000]], "query") if query.strip() else None

    scored = []
    for p, d in rows:
        ev = evaluate(d.extracted_data or {}, p, criteria)
        sim = embeddings.cosine(qv[0], p.embedding) if qv and p.embedding and p.embedding_model == embeddings.model_name() else 0.0
        s = ev["summary"]
        # Tri explicable : indispensables remplis, puis à confirmer, puis souhaités ; la proximité sémantique ne départage qu'à égalité
        scored.append(((-s["must_met"], -s["must_to_confirm"], -s["nice_met"], -sim), p, d, ev))
    scored.sort(key=lambda x: x[0])
    return [{**search.hit(p, d, anonymous), **ev} for _, p, d, ev in scored[:30]]
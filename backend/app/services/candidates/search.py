import math
from collections import Counter
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import CandidateProfile, Document, DocumentStatus
from app.services.candidates import embeddings, skills
from app.services.candidates.anonymize import display_name

STOP = {"le", "la", "les", "de", "du", "des", "un", "une", "et", "en", "au", "aux", "pour", "avec", "sur", "dans",
        "par", "ou", "the", "an", "of", "and", "in", "for", "with", "to", "on", "at", "or"}


def _toks(text: str) -> List[str]:
    return [t for t in skills.tokens(text) if len(t) > 1 and t not in STOP]


def expand_query(q: str) -> str:
    """Ajoute le nom canonique des compétences citées par un synonyme (ML devient Machine Learning)."""
    f = skills.fold(q)
    return q + " " + " ".join(c for c in skills.ALIASES if skills.mentioned(c, f))


def bm25(query: List[str], docs: List[List[str]], k1: float = 1.5, b: float = 0.75) -> List[float]:
    n = len(docs)
    avgdl = (sum(len(d) for d in docs) / n) if n else 1
    df = Counter(t for d in docs for t in set(d))
    out = []
    for d in docs:
        tf, score = Counter(d), 0.0
        for t in set(query):
            if t in tf:
                idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
                score += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * len(d) / (avgdl or 1)))
        out.append(score)
    return out


def _ranks(scores: List[float]) -> dict:
    order = sorted((i for i, s in enumerate(scores) if s > 0), key=lambda i: -scores[i])
    return {i: r for r, i in enumerate(order, 1)}


def load_candidates(db: Session, company_id: int) -> List[Tuple[CandidateProfile, Document]]:
    return (
        db.query(CandidateProfile, Document)
        .join(Document, Document.id == CandidateProfile.document_id)
        .filter(CandidateProfile.company_id == company_id, Document.status == DocumentStatus.DONE)
        .all()
    )


def unindexed_count(db: Session, company_id: int, indexed: int) -> int:
    total = db.query(Document).filter(
        Document.company_id == company_id, Document.doc_type == "cv", Document.status == DocumentStatus.DONE
    ).count()
    return max(total - indexed, 0)


def hit(p: CandidateProfile, d: Document, anonymous: bool, reasons: Optional[list] = None) -> dict:
    data = d.extracted_data or {}
    return {
        "document_id": d.id,
        "name": display_name(d.id, data, anonymous),
        "headline": data.get("headline"),
        "location": data.get("location"),
        "years": round(p.years or 0, 1),
        "job_family": p.job_family,
        "skills": list(p.skills or [])[:10],
        "languages": [l.get("language") for l in data.get("languages") or [] if l.get("language")],
        "reasons": reasons or [],
    }


def search(db: Session, company_id: int, q: str, min_years: Optional[float], skill_filters: List[str],
           language: Optional[str], location: Optional[str], anonymous: bool) -> dict:
    rows = load_candidates(db, company_id)
    kept = []
    for p, d in rows:
        data = d.extracted_data or {}
        folded = skills.fold(p.search_text)
        if min_years and (p.years or 0) < min_years:
            continue
        if any(not skills.mentioned(s, folded) for s in skill_filters):
            continue
        if language and not any(skills.fold(language) in skills.fold(l.get("language") or "") for l in data.get("languages") or []):
            continue
        if location and skills.fold(location) not in skills.fold(data.get("location") or ""):
            continue
        kept.append((p, d))

    semantic = False
    ordered = sorted(kept, key=lambda pd: pd[0].updated_at, reverse=True)
    reasons: dict = {}
    if q and kept:
        qtoks = _toks(expand_query(q))
        docs = [_toks(p.search_text) for p, _ in kept]
        lex = bm25(qtoks, docs)
        ranks = [_ranks(lex)]

        qv = embeddings.embed([q], "query")
        sims = [embeddings.cosine(qv[0], p.embedding) if qv and p.embedding and p.embedding_model == embeddings.model_name() else 0.0
                for p, _ in kept]
        sem_ranks = _ranks(sims) if qv else {}
        if sem_ranks:
            semantic = True
            ranks.append(sem_ranks)

        fused = [sum(1 / (60 + r[i]) for r in ranks if i in r) for i in range(len(kept))]
        ordered_idx = [i for i in sorted(range(len(kept)), key=lambda i: -fused[i]) if fused[i] > 0]
        ordered = [kept[i] for i in ordered_idx]
        fq = skills.fold(q)
        for i in ordered_idx:
            p, d = kept[i]
            found = [t for t in dict.fromkeys(qtoks) if t in set(docs[i])][:6]
            r = [f"Compétence : {s}" for s in (p.skills or []) if skills.mentioned(s, fq)][:4]
            if found:
                r.append("Termes : " + ", ".join(found))
            if i in sem_ranks and sem_ranks[i] <= max(3, len(kept) // 5):
                r.append("Profil proche (sémantique)")
            reasons[d.id] = r

    return {
        "items": [hit(p, d, anonymous, reasons.get(d.id)) for p, d in ordered[:50]],
        "unindexed": unindexed_count(db, company_id, len(rows)),
        "semantic": semantic,
    }
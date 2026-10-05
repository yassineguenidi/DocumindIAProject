import re
import unicodedata
from typing import Literal, Optional, Tuple

from pydantic import BaseModel

from app.core.config import settings
from app.services.pipeline import llm
from app.services.pipeline.reader import ReadResult
from app.services.pipeline.registry import CLASSES

# Mots-clés par type et par langue, écrits sans accents. Ajouter une langue = ajouter une clé.
KEYWORDS = {
    "invoice": {
        "fr": ["facture", "total ttc", "montant ht", "tva", "echeance", "siret", "net a payer"],
        "en": ["invoice", "subtotal", "bill to", "billed to", "due date", "invoice no", "total due", "amount due", "vat", "sales tax"],
    },
    "cv": {
        "fr": ["curriculum", "experience professionnelle", "experiences professionnelles", "competences", "formation", "langues", "centres d'interet"],
        "en": ["resume", "curriculum vitae", "work experience", "professional experience", "skills", "education", "languages", "references"],
    },
    "contract": {
        "fr": ["contrat", "entre les soussignes", "article 1", "clause", "resiliation", "il a ete convenu"],
        "en": ["agreement", "hereby", "whereas", "clause", "termination", "governing law", "the parties"],
    },
    "id": {
        "fr": ["carte nationale d'identite", "passeport", "nationalite", "republique francaise"],
        "en": ["passport", "identity card", "nationality", "date of birth"],
    },
}

TASK = (
    "Quel est le type de ce document ? invoice (facture ou avoir), cv, contract (contrat de travail, bail...), "
    "id (pièce d'identité), other (tout le reste). Le document peut être en français ou en anglais."
)


class DocClass(BaseModel):
    doc_type: Literal["invoice", "cv", "contract", "id", "other"]  # même liste que CLASSES


def _fold(s: str) -> str:
    """Minuscules, sans accents, apostrophes normalisées."""
    s = unicodedata.normalize("NFKD", s.lower().replace("’", "'"))
    return "".join(ch for ch in s if not unicodedata.combining(ch))


# Un motif par mot-clé, avec limites de mot (évite « vat » dans « innovation »)
_PATTERNS = {
    kind: [re.compile(rf"\b{re.escape(_fold(kw))}\b") for kws in langs.values() for kw in kws]
    for kind, langs in KEYWORDS.items()
}


def _by_rules(text: str) -> Optional[str]:
    t = _fold(text)
    scores = sorted(
        ((sum(1 for p in pats if p.search(t)), kind) for kind, pats in _PATTERNS.items()),
        reverse=True,
    )
    (best, kind), (second, _) = scores[0], scores[1]
    return kind if best >= 2 and best > second else None


def classify(doc: ReadResult) -> Tuple[str, Optional[llm.LLMResult]]:
    if doc.mode == "text":
        kind = _by_rules(doc.text)
        if kind:
            return kind, None
    res = llm.call_tool(settings.LLM_MODEL_FAST, "classify_document", "Indique le type du document",
                        DocClass, doc, TASK, max_tokens=200)
    kind = res.data.get("doc_type")
    return (kind if kind in CLASSES else "other"), res



# from typing import Literal, Optional, Tuple

# from pydantic import BaseModel

# from app.core.config import settings
# from app.services.pipeline import llm
# from app.services.pipeline.reader import ReadResult
# from app.services.pipeline.registry import CLASSES

# KEYWORDS = {
#     "invoice": ["facture", "invoice", "total ttc", "montant ht", "tva", "échéance", "siret", "avoir"],
#     "cv": ["curriculum", "expérience professionnelle", "expériences professionnelles", "compétences", "formation", "langues"],
#     "contract": ["contrat", "entre les soussignés", "article 1", "clause", "résiliation"],
#     "id": ["carte nationale d'identité", "passeport", "nationalité", "république française"],
# }

# TASK = (
#     "Quel est le type de ce document ? invoice (facture ou avoir), cv, contract (contrat de travail, bail...), "
#     "id (pièce d'identité), other (tout le reste)."
# )


# class DocClass(BaseModel):
#     doc_type: Literal["invoice", "cv", "contract", "id", "other"]  # même liste que CLASSES


# def _by_rules(text: str) -> Optional[str]:
#     t = text.lower()
#     scores = sorted(((sum(kw in t for kw in kws), kind) for kind, kws in KEYWORDS.items()), reverse=True)
#     (best, kind), (second, _) = scores[0], scores[1]
#     return kind if best >= 2 and best > second else None


# def classify(doc: ReadResult) -> Tuple[str, Optional[llm.LLMResult]]:
#     if doc.mode == "text":
#         kind = _by_rules(doc.text)
#         if kind:
#             return kind, None
#     res = llm.call_tool(settings.LLM_MODEL_FAST, "classify_document", "Indique le type du document",
#                         DocClass, doc, TASK, max_tokens=200)
#     kind = res.data.get("doc_type")
#     return (kind if kind in CLASSES else "other"), res

# # from typing import Optional, Tuple

# # from app.core.config import settings
# # from app.services.pipeline import llm
# # from app.services.pipeline.reader import ReadResult
# # from app.services.pipeline.registry import CLASSES

# # KEYWORDS = {
# #     "invoice": ["facture", "invoice", "total ttc", "montant ht", "tva", "échéance", "siret", "avoir"],
# #     "cv": ["curriculum", "expérience professionnelle", "expériences professionnelles", "compétences", "formation", "langues"],
# #     "contract": ["contrat", "entre les soussignés", "article 1", "clause", "résiliation"],
# #     "id": ["carte nationale d'identité", "passeport", "nationalité", "république française"],
# # }

# # SCHEMA = {
# #     "type": "object",
# #     "properties": {"doc_type": {"type": "string", "enum": CLASSES}},
# #     "required": ["doc_type"],
# # }
# # TASK = (
# #     "Quel est le type de ce document ? invoice (facture ou avoir), cv, contract (contrat de travail, bail...), "
# #     "id (pièce d'identité), other (tout le reste)."
# # )


# # def _by_rules(text: str) -> Optional[str]:
# #     t = text.lower()
# #     scores = sorted(((sum(kw in t for kw in kws), kind) for kind, kws in KEYWORDS.items()), reverse=True)
# #     (best, kind), (second, _) = scores[0], scores[1]
# #     return kind if best >= 2 and best > second else None


# # def classify(doc: ReadResult) -> Tuple[str, Optional[llm.LLMResult]]:
# #     if doc.mode == "text":
# #         kind = _by_rules(doc.text)
# #         if kind:
# #             return kind, None
# #     res = llm.call_tool(settings.LLM_MODEL_FAST, "classify_document", "Indique le type du document",
# #                         SCHEMA, doc, TASK, max_tokens=200)
# #     kind = res.data.get("doc_type")
# #     return (kind if kind in CLASSES else "other"), res
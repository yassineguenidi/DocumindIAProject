import re
import unicodedata
from typing import Literal, Optional, Tuple

from pydantic import BaseModel

from app.core.config import settings
from app.services.pipeline import llm
from app.services.pipeline.reader import ReadResult
from app.services.pipeline.registry import CLASSES, TYPE_INFO

# Mots-clés par type et par langue, écrits sans accents. Ajouter une langue = ajouter une clé.
KEYWORDS = {
    "invoice": {
        "fr": ["facture", "total ttc", "montant ht", "tva", "echeance", "siret", "net a payer"],
        "en": ["invoice", "subtotal", "bill to", "billed to", "due date", "invoice no", "total due", "amount due", "vat", "sales tax"],
    },
    "quote": {
        "fr": ["devis", "bon pour accord", "validite de l'offre", "offre de prix", "valable jusqu"],
        "en": ["quotation", "quote no", "estimate", "valid until"],
    },
    "purchase_order": {
        "fr": ["bon de commande", "commande fournisseur", "livraison souhaitee", "date de commande"],
        "en": ["purchase order", "po number", "order date"],
    },
    "delivery_note": {
        "fr": ["bon de livraison", "quantite livree", "quantites livrees", "date de livraison", "bon de reception"],
        "en": ["delivery note", "packing slip", "goods received"],
    },
    "expense_receipt": {
        "fr": ["ticket de caisse", "merci de votre visite", "carte bancaire", "especes", "note de restaurant"],
        "en": ["receipt", "thank you for your visit", "card payment", "cash"],
    },
    "bank_statement": {
        "fr": ["releve de compte", "releve bancaire", "ancien solde", "nouveau solde", "solde initial", "solde final", "solde precedent"],
        "en": ["bank statement", "account statement", "opening balance", "closing balance"],
    },
    "bank_details": {
        "fr": ["releve d'identite bancaire", "rib", "titulaire du compte", "domiciliation", "code banque", "code guichet", "cle rib"],
        "en": ["bank details", "account holder", "swift"],
    },
    "company_registration": {
        "fr": ["extrait kbis", "kbis", "registre du commerce et des societes", "greffe", "forme juridique", "capital social", "immatriculation"],
        "en": ["certificate of incorporation", "company registration"],
    },
    "vigilance_certificate": {
        "fr": ["attestation de vigilance", "urssaf", "code de securite", "contributions et cotisations sociales"],
        "en": [],
    },
    "cv": {
        "fr": ["curriculum", "experience professionnelle", "experiences professionnelles", "competences", "formation", "langues", "centres d'interet"],
        "en": ["resume", "curriculum vitae", "work experience", "professional experience", "skills", "education", "languages", "references"],
    },
    "job_description": {
        "fr": ["fiche de poste", "offre d'emploi", "profil recherche", "competences requises", "nous recherchons", "poste a pourvoir", "type de contrat"],
        "en": ["job description", "job offer", "we are looking for", "responsibilities", "requirements", "qualifications"],
    },
    "employment_contract": {
        "fr": ["contrat de travail", "contrat a duree indeterminee", "contrat a duree determinee", "periode d'essai", "l'employeur", "le salarie",
               "convention collective", "preavis", "avenant"],
        "en": ["employment agreement", "employment contract", "probation", "the employer", "the employee"],
    },
    "payslip": {
        "fr": ["bulletin de paie", "bulletin de salaire", "fiche de paie", "salaire brut", "net imposable", "cotisations",
               "prelevement a la source", "conges payes"],
        "en": ["payslip", "pay slip", "gross pay", "net pay", "gross salary", "net salary", "deductions"],
    },
    "tax_notice": {
        "fr": ["avis d'impot", "avis d'imposition", "revenu fiscal de reference", "direction generale des finances publiques",
               "impot sur le revenu", "nombre de parts", "numero fiscal", "avis de non-imposition"],
        "en": ["tax assessment", "notice of assessment"],
    },
    "proof_of_address": {
        "fr": ["quittance de loyer", "quittance", "avoir recu", "attestation d'hebergement", "heberge a titre gratuit",
               "heberger a titre gratuit", "attestation d'assurance habitation", "avis de taxe fonciere", "taxe fonciere",
               "justificatif de domicile"],
        "en": ["proof of address", "rent receipt", "accommodation certificate"],
    },
    "id": {
        "fr": ["carte nationale d'identite", "passeport", "nationalite", "republique francaise", "titre de sejour", "permis de conduire"],
        "en": ["passport", "identity card", "nationality", "residence permit", "driving licence"],
    },
    "lease": {
        "fr": ["contrat de location", "bail", "bailleur", "locataire", "depot de garantie", "charges locatives", "bail d'habitation"],
        "en": ["lease agreement", "landlord", "tenant", "security deposit"],
    },
    "property_mandate": {
        "fr": ["mandat de vente", "mandat de gestion", "mandat de recherche", "mandat exclusif", "mandat simple", "registre des mandats",
               "honoraires", "mandant", "mandataire", "carte professionnelle"],
        "en": ["listing agreement", "exclusive agency"],
    },
    "diagnostic_report": {
        "fr": ["diagnostic de performance energetique", "dpe", "amiante", "diagnostic", "etat des risques", "diagnostiqueur",
               "consommation energetique", "emissions de gaz a effet de serre", "plomb", "termites"],
        "en": ["energy performance certificate", "epc"],
    },
    "inventory": {
        "fr": ["etat des lieux", "etat des lieux d'entree", "etat des lieux de sortie", "releve des compteurs", "cles remises", "etat d'usage"],
        "en": ["inventory report", "move-in", "check-in report", "condition report"],
    },
    "non_requestable": {
        "fr": ["carte vitale", "attestation de droits", "casier judiciaire", "livret de famille", "contrat de mariage", "pacs",
               "jugement de divorce", "dossier medical", "attestation de bonne tenue de compte", "autorisation de prelevement",
               "cheque de reservation"],
        "en": [],
    },
    "contract": {
        "fr": ["contrat", "entre les soussignes", "article 1", "clause", "resiliation", "il a ete convenu"],
        "en": ["agreement", "hereby", "whereas", "termination", "governing law", "the parties"],
    },
}
MIN_HITS = {"non_requestable": 1}  # un seul indice suffit pour signaler une pièce non exigible
MRZ_RE = re.compile(r"[A-Z0-9<]{20,}<<[A-Z0-9<]*")

TASK = (
    "Quel est le type de ce document ? Choisis exactement UNE valeur :\n"
    + "\n".join(f"- {code} : {info['hint']}" for code, info in TYPE_INFO.items())
    + "\nUne facture d'énergie, d'eau ou de téléphone est une invoice. Le document peut être en français ou en anglais."
)


class DocClass(BaseModel):
    doc_type: Literal[tuple(CLASSES)]  # type: ignore[valid-type]  # même liste que CLASSES


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
    if MRZ_RE.search(text):  # zone lisible par machine d'une pièce d'identité
        return "id"
    t = _fold(text)
    scores = sorted(
        ((sum(1 for p in pats if p.search(t)), kind) for kind, pats in _PATTERNS.items()),
        reverse=True,
    )
    (best, kind), (second, _) = scores[0], scores[1]
    return kind if best >= MIN_HITS.get(kind, 2) and best > second else None


def classify(doc: ReadResult) -> Tuple[str, Optional[llm.LLMResult]]:
    if doc.mode == "text":
        kind = _by_rules(doc.text)
        if kind:
            return kind, None
    res = llm.call_tool(settings.LLM_MODEL_FAST, "classify_document", "Indique le type du document",
                        DocClass, doc, TASK, max_tokens=200)
    kind = res.data.get("doc_type")
    return (kind if kind in CLASSES else "other"), res












# import re
# import unicodedata
# from typing import Literal, Optional, Tuple

# from pydantic import BaseModel

# from app.core.config import settings
# from app.services.pipeline import llm
# from app.services.pipeline.reader import ReadResult
# from app.services.pipeline.registry import CLASSES

# # Mots-clés par type et par langue, écrits sans accents. Ajouter une langue = ajouter une clé.
# KEYWORDS = {
#     "invoice": {
#         "fr": ["facture", "total ttc", "montant ht", "tva", "echeance", "siret", "net a payer"],
#         "en": ["invoice", "subtotal", "bill to", "billed to", "due date", "invoice no", "total due", "amount due", "vat", "sales tax"],
#     },
#     "cv": {
#         "fr": ["curriculum", "experience professionnelle", "experiences professionnelles", "competences", "formation", "langues", "centres d'interet"],
#         "en": ["resume", "curriculum vitae", "work experience", "professional experience", "skills", "education", "languages", "references"],
#     },
#     "contract": {
#         "fr": ["contrat", "entre les soussignes", "article 1", "clause", "resiliation", "il a ete convenu"],
#         "en": ["agreement", "hereby", "whereas", "clause", "termination", "governing law", "the parties"],
#     },
#     "id": {
#         "fr": ["carte nationale d'identite", "passeport", "nationalite", "republique francaise"],
#         "en": ["passport", "identity card", "nationality", "date of birth"],
#     },
# }

# TASK = (
#     "Quel est le type de ce document ? invoice (facture ou avoir), cv, contract (contrat de travail, bail...), "
#     "id (pièce d'identité), other (tout le reste). Le document peut être en français ou en anglais."
# )


# class DocClass(BaseModel):
#     doc_type: Literal["invoice", "cv", "contract", "id", "other"]  # même liste que CLASSES


# def _fold(s: str) -> str:
#     """Minuscules, sans accents, apostrophes normalisées."""
#     s = unicodedata.normalize("NFKD", s.lower().replace("’", "'"))
#     return "".join(ch for ch in s if not unicodedata.combining(ch))


# # Un motif par mot-clé, avec limites de mot (évite « vat » dans « innovation »)
# _PATTERNS = {
#     kind: [re.compile(rf"\b{re.escape(_fold(kw))}\b") for kws in langs.values() for kw in kws]
#     for kind, langs in KEYWORDS.items()
# }


# def _by_rules(text: str) -> Optional[str]:
#     t = _fold(text)
#     scores = sorted(
#         ((sum(1 for p in pats if p.search(t)), kind) for kind, pats in _PATTERNS.items()),
#         reverse=True,
#     )
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



# # from typing import Literal, Optional, Tuple

# # from pydantic import BaseModel

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

# # TASK = (
# #     "Quel est le type de ce document ? invoice (facture ou avoir), cv, contract (contrat de travail, bail...), "
# #     "id (pièce d'identité), other (tout le reste)."
# # )


# # class DocClass(BaseModel):
# #     doc_type: Literal["invoice", "cv", "contract", "id", "other"]  # même liste que CLASSES


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
# #                         DocClass, doc, TASK, max_tokens=200)
# #     kind = res.data.get("doc_type")
# #     return (kind if kind in CLASSES else "other"), res

# # # from typing import Optional, Tuple

# # # from app.core.config import settings
# # # from app.services.pipeline import llm
# # # from app.services.pipeline.reader import ReadResult
# # # from app.services.pipeline.registry import CLASSES

# # # KEYWORDS = {
# # #     "invoice": ["facture", "invoice", "total ttc", "montant ht", "tva", "échéance", "siret", "avoir"],
# # #     "cv": ["curriculum", "expérience professionnelle", "expériences professionnelles", "compétences", "formation", "langues"],
# # #     "contract": ["contrat", "entre les soussignés", "article 1", "clause", "résiliation"],
# # #     "id": ["carte nationale d'identité", "passeport", "nationalité", "république française"],
# # # }

# # # SCHEMA = {
# # #     "type": "object",
# # #     "properties": {"doc_type": {"type": "string", "enum": CLASSES}},
# # #     "required": ["doc_type"],
# # # }
# # # TASK = (
# # #     "Quel est le type de ce document ? invoice (facture ou avoir), cv, contract (contrat de travail, bail...), "
# # #     "id (pièce d'identité), other (tout le reste)."
# # # )


# # # def _by_rules(text: str) -> Optional[str]:
# # #     t = text.lower()
# # #     scores = sorted(((sum(kw in t for kw in kws), kind) for kind, kws in KEYWORDS.items()), reverse=True)
# # #     (best, kind), (second, _) = scores[0], scores[1]
# # #     return kind if best >= 2 and best > second else None


# # # def classify(doc: ReadResult) -> Tuple[str, Optional[llm.LLMResult]]:
# # #     if doc.mode == "text":
# # #         kind = _by_rules(doc.text)
# # #         if kind:
# # #             return kind, None
# # #     res = llm.call_tool(settings.LLM_MODEL_FAST, "classify_document", "Indique le type du document",
# # #                         SCHEMA, doc, TASK, max_tokens=200)
# # #     kind = res.data.get("doc_type")
# # #     return (kind if kind in CLASSES else "other"), res
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Type

from pydantic import BaseModel

from app.schemas.cv import CVData
from app.schemas.invoice import InvoiceData
from app.services.pipeline import enrichers, validators

# Types reconnus par la classification (même ceux qu'on ne sait pas encore extraire)
CLASSES = ["invoice", "cv", "contract", "id", "other"]


@dataclass(frozen=True)
class DocTypeDef:
    code: str
    label: str
    schema: Type[BaseModel]
    instructions: str
    validate: Callable[[dict, str], List[dict]]
    enrich: Optional[Callable[[dict], dict]] = None


INVOICE = DocTypeDef(
    code="invoice",
    label="facture",
    schema=InvoiceData,
    instructions=(
        "Il s'agit d'une facture ou d'un avoir, en français ou en anglais (ou une autre langue). "
        "Nombres : renvoie toujours un nombre avec point décimal, sans symbole ni séparateur de milliers. "
        "Déduis le format de la langue du document : 1 234,56 € (français) et 1,234.56 $ (anglais) valent tous deux 1234.56. "
        "Dates au format AAAA-MM-JJ. Si le format est ambigu (03/04/2025), déduis JJ/MM ou MM/JJ de la langue et du pays "
        "du document (adresse, devise, mentions). "
        "currency : code ISO déduit du symbole ou du texte (€ = EUR, $ = USD, £ = GBP), sinon null. "
        "language : langue principale du document (fr, en...). "
        "Correspondances : sous-total / subtotal = total_ht ; TVA / VAT / tax / sales tax = total_vat ; "
        "total TTC / total / amount due / balance due = total_ttc ; "
        "facturé à / bill to = client ; émis par / from / issued by = fournisseur. "
        "Taux de TVA en pourcentage (20 pour 20 %). "
        "Ne recalcule aucun montant : recopie ceux du document. "
        "Mets document_kind à credit_note pour un avoir (credit note)."
    ),
    validate=validators.validate_invoice,
)

CV = DocTypeDef(
    code="cv",
    label="CV",
    schema=CVData,
    instructions=(
        "Il s'agit d'un CV, en français ou en anglais (ou une autre langue). Extrais uniquement ce qui est écrit. "
        "Ne renseigne JAMAIS l'âge, la date de naissance, le genre, la nationalité, la situation familiale, les enfants, "
        "l'état de santé, ni aucune information sur l'origine ou la photo : ces données sont volontairement ignorées, "
        "y compris dans le résumé et les descriptions. "
        "location : ville et pays seulement, jamais l'adresse complète. "
        "email et phone : recopie-les tels qu'écrits. "
        "Dates au format AAAA-MM (AAAA si le mois est absent). Pour un poste en cours (présent, aujourd'hui, en cours, "
        "current, present), mets is_current à true et end_date à null. "
        "skills : uniquement des compétences explicitement écrites ; source skills_section si elles figurent dans une rubrique "
        "de compétences, sinon experience. N'invente et ne déduis aucune compétence. "
        "Une entrée par poste, formation, langue et certification, dans l'ordre du document. "
        "language : langue principale du CV (fr, en...)."
    ),
    validate=validators.validate_cv,
    enrich=enrichers.cv_derived,
)

# Ajouter un type = ajouter une définition ici
REGISTRY: Dict[str, DocTypeDef] = {d.code: d for d in (INVOICE, CV)}
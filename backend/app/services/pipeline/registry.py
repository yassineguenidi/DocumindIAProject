from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Type

from pydantic import BaseModel

from app.core.config import settings
from app.schemas.cv import CVData
from app.schemas.invoice import InvoiceData
from app.schemas.personal_docs import (
    EmploymentContractData, IdentityDocumentData, JobDescriptionData, PayslipData, ProofOfAddressData, TaxNoticeData,
)
from app.services.pipeline import enrichers, validators

SECTORS = [
    {"code": "hr", "label": "RH"},
    {"code": "finance", "label": "Finance"},
    {"code": "realestate", "label": "Immobilier"},
]

# Métadonnées de TOUS les types reconnus par la classification (même ceux qu'on ne sait pas encore extraire).
# sensitivity : standard | high | very_high (very_high = réservé aux administrateurs)
TYPE_INFO: Dict[str, dict] = {
    "invoice": {"label": "Facture", "sectors": ["finance"], "sensitivity": "standard",
                "hint": "facture ou avoir fournisseur ou client, y compris facture d'énergie, d'eau ou de téléphone"},
    "quote": {"label": "Devis", "sectors": ["finance"], "sensitivity": "standard", "hint": "devis ou offre de prix"},
    "purchase_order": {"label": "Bon de commande", "sectors": ["finance"], "sensitivity": "standard", "hint": "bon de commande"},
    "delivery_note": {"label": "Bon de livraison", "sectors": ["finance"], "sensitivity": "standard", "hint": "bon de livraison ou de réception"},
    "expense_receipt": {"label": "Note de frais / ticket", "sectors": ["finance"], "sensitivity": "standard",
                        "hint": "ticket de caisse, reçu ou justificatif de dépense (restaurant, transport, hôtel, carburant)"},
    "bank_statement": {"label": "Relevé bancaire", "sectors": ["finance"], "sensitivity": "high", "hint": "relevé de compte bancaire"},
    "bank_details": {"label": "RIB", "sectors": ["finance", "hr"], "sensitivity": "high", "hint": "relevé d'identité bancaire (RIB) ou coordonnées bancaires"},
    "company_registration": {"label": "Extrait Kbis", "sectors": ["finance"], "sensitivity": "standard", "hint": "extrait Kbis ou d'immatriculation d'entreprise"},
    "vigilance_certificate": {"label": "Attestation de vigilance", "sectors": ["finance"], "sensitivity": "standard",
                              "hint": "attestation de vigilance URSSAF"},
    "cv": {"label": "CV", "sectors": ["hr"], "sensitivity": "high", "hint": "CV, curriculum vitae ou resume"},
    "job_description": {"label": "Fiche de poste", "sectors": ["hr"], "sensitivity": "standard", "hint": "fiche de poste ou offre d'emploi"},
    "employment_contract": {"label": "Contrat de travail", "sectors": ["hr", "realestate"], "sensitivity": "high",
                            "hint": "contrat de travail (CDI, CDD, intérim, alternance, stage) ou avenant"},
    "payslip": {"label": "Bulletin de paie", "sectors": ["hr", "realestate"], "sensitivity": "high", "hint": "bulletin de paie ou fiche de paie (payslip)"},
    "tax_notice": {"label": "Avis d'imposition", "sectors": ["finance", "realestate"], "sensitivity": "high",
                   "hint": "avis d'imposition ou de non-imposition sur le revenu"},
    "proof_of_address": {"label": "Justificatif de domicile", "sectors": ["hr", "realestate"], "sensitivity": "high",
                         "hint": "justificatif de domicile autre qu'une facture : quittance de loyer, attestation d'hébergement, attestation d'assurance habitation, avis de taxe foncière"},
    "id": {"label": "Pièce d'identité", "sectors": ["hr", "realestate"], "sensitivity": "very_high",
           "hint": "pièce d'identité : carte d'identité, passeport, permis de conduire, titre de séjour"},
    "lease": {"label": "Bail", "sectors": ["realestate"], "sensitivity": "high", "hint": "bail ou contrat de location de logement"},
    "property_mandate": {"label": "Mandat", "sectors": ["realestate"], "sensitivity": "high", "hint": "mandat de vente, de gestion ou de recherche immobilière"},
    "diagnostic_report": {"label": "Diagnostic (DPE…)", "sectors": ["realestate"], "sensitivity": "standard",
                          "hint": "diagnostic immobilier : DPE, amiante, plomb, électricité, gaz, état des risques, termites"},
    "inventory": {"label": "État des lieux", "sectors": ["realestate"], "sensitivity": "high", "hint": "état des lieux d'entrée ou de sortie"},
    "non_requestable": {"label": "Pièce non exigible (location)", "sectors": ["realestate"], "sensitivity": "very_high",
                        "hint": "pièce qu'un propriétaire ne peut pas exiger d'un candidat locataire : carte Vitale, extrait de casier judiciaire, livret de famille, contrat de mariage ou PACS, jugement de divorce, dossier médical, attestation de bonne tenue de compte, autorisation de prélèvement, chèque de réservation"},
    "contract": {"label": "Autre contrat", "sectors": ["realestate"], "sensitivity": "high", "hint": "tout autre contrat : commercial, de vente, de prestation"},
    "other": {"label": "Autre", "sectors": [], "sensitivity": "standard", "hint": "tout le reste : courrier, brochure, document illisible"},
}
CLASSES: List[str] = list(TYPE_INFO)


@dataclass(frozen=True)
class DocTypeDef:
    code: str
    label: str
    schema: Type[BaseModel]
    instructions: str
    validate: Callable[[dict, str], List[dict]]
    enrich: Optional[Callable[[dict], dict]] = None
    finalize: Optional[Callable[[dict], None]] = None  # appelé sur le résultat retenu, avant l'enregistrement


NUMBERS = (
    "Nombres : renvoie toujours un nombre avec point décimal, sans symbole ni séparateur de milliers "
    "(1 234,56 € en français et 1,234.56 $ en anglais valent tous deux 1234.56). "
    "Dates au format AAAA-MM-JJ ; si le format est ambigu (03/04/2025), déduis JJ/MM ou MM/JJ de la langue et du pays du document. "
    "Le document peut être en français ou en anglais. language : langue principale (fr, en...). Ne recalcule aucun montant : recopie ceux du document. "
)
PRIVACY = (
    "N'extrais JAMAIS le numéro de sécurité sociale, la date ou le lieu de naissance, la nationalité, la situation familiale, "
    "l'état de santé, les coordonnées bancaires personnelles ni l'adresse personnelle complète, sauf si un champ le demande explicitement. "
)

INSTRUCTIONS = {
    "invoice": (
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
        "purchase_order_ref : référence de commande ou de bon de commande citée par la facture. "
        "Taux de TVA en pourcentage (20 pour 20 %). "
        "Ne recalcule aucun montant : recopie ceux du document. "
        "Mets document_kind à credit_note pour un avoir (credit note)."
    ),
    "cv": (
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
    "payslip": (
        "Il s'agit d'un bulletin de paie (fiche de paie) français. " + NUMBERS + PRIVACY +
        "period_start et period_end : période de paie (du 01/09 au 30/09 → 2026-09-01 et 2026-09-30). "
        "gross_salary : salaire brut du mois. net_before_tax : « net à payer avant impôt sur le revenu ». "
        "net_taxable : net imposable du mois. income_tax_withheld : montant de l'impôt sur le revenu prélevé à la source ce mois (0 si aucun). "
        "net_paid : « net payé » ou « net à payer » versé au salarié après impôt. ytd_net_taxable : cumul annuel du net imposable."
    ),
    "employment_contract": (
        "Il s'agit d'un contrat de travail (ou d'un avenant). " + NUMBERS + PRIVACY +
        "contract_type : cdi, cdd, interim, apprenticeship (alternance, apprentissage, professionnalisation), internship (stage) ou other. "
        "trial_period, working_hours et notice_period : recopie les termes du contrat. "
        "gross_salary et salary_period (month, year ou hour) : rémunération brute principale. "
        "work_location : ville seulement. special_clauses : libellés courts des clauses particulières PRÉSENTES "
        "(non-concurrence, mobilité, confidentialité, exclusivité, dédit-formation, forfait jours...)."
    ),
    "tax_notice": (
        "Il s'agit d'un avis d'impôt sur le revenu ou de non-imposition (France). " + NUMBERS + PRIVACY +
        "N'extrais JAMAIS le numéro fiscal, le numéro d'accès en ligne ni la référence de l'avis ; pour l'adresse, seulement code postal et ville. "
        "income_year : année des revenus (« revenus de 2025 »). issue_year : année de l'avis (« avis d'impôt 2026 »). "
        "fiscal_reference_income : revenu fiscal de référence. household_parts : nombre de parts. "
        "income_tax_amount : montant de l'impôt sur le revenu net. non_taxable : true pour un avis de non-imposition."
    ),
    "proof_of_address": (
        "Il s'agit d'un justificatif de domicile. " + NUMBERS + PRIVACY +
        "kind : utility_bill (facture d'énergie, d'eau, de téléphone), rent_receipt (quittance de loyer), property_tax (taxe foncière), "
        "hosting_certificate (attestation d'hébergement), home_insurance (attestation d'assurance habitation) ou other. "
        "holder_name : la personne dont l'adresse est justifiée (l'hébergé pour une attestation d'hébergement) ; host_name : l'hébergeant. "
        "issuer : fournisseur, bailleur, assureur ou administration. address_line, postal_code, city : adresse du logement justifié."
    ),
    "id": (
        "Il s'agit d'une pièce d'identité (carte d'identité, passeport, permis de conduire ou titre de séjour). " + NUMBERS +
        "N'extrais JAMAIS le numéro du document, la date ni le lieu de naissance, le sexe, la nationalité ni l'adresse. "
        "Extrais seulement : document_kind, issuing_country, last_name, first_names, issue_date, expiry_date. "
        "mrz_lines : recopie EXACTEMENT, caractère par caractère, les lignes de la zone lisible par machine (celles qui contiennent des « < »), "
        "ou une liste vide s'il n'y en a pas. Ne les corrige pas."
    ),
    "job_description": (
        "Il s'agit d'une fiche de poste ou d'une offre d'emploi. " + NUMBERS +
        "must_have : compétences, outils ou qualifications indispensables, une par entrée, formulées de façon courte. "
        "nice_to_have : atouts souhaités. min_years : expérience minimale demandée. languages : langues exigées. "
        "N'inclus AUCUN critère d'âge, de genre, de nationalité, de situation familiale, d'état de santé ou d'apparence."
    ),
}

_DEFS = [
    ("invoice", "facture", InvoiceData, validators.validate_invoice, None, None),
    ("cv", "CV", CVData, validators.validate_cv, enrichers.cv_derived, None),
    ("payslip", "bulletin de paie", PayslipData, validators.validate_payslip, None, None),
    ("employment_contract", "contrat de travail", EmploymentContractData, validators.validate_employment_contract, None, None),
    ("tax_notice", "avis d'imposition", TaxNoticeData, validators.validate_tax_notice, None, None),
    ("proof_of_address", "justificatif de domicile", ProofOfAddressData, validators.validate_proof_of_address, None, None),
    ("id", "pièce d'identité", IdentityDocumentData, validators.validate_id, None, validators.finalize_id),
    ("job_description", "fiche de poste", JobDescriptionData, validators.validate_job_description, None, None),
]

# Ajouter un type = une entrée dans TYPE_INFO, une dans INSTRUCTIONS et une ligne dans _DEFS
REGISTRY: Dict[str, DocTypeDef] = {
    code: DocTypeDef(code, label, schema, INSTRUCTIONS[code], validate, enrich, finalize)
    for code, label, schema, validate, enrich, finalize in _DEFS
}


def type_catalog() -> dict:
    return {
        "sectors": SECTORS,
        "types": [
            {"code": code, "label": info["label"], "sectors": info["sectors"],
             "sensitivity": info["sensitivity"], "extractable": code in REGISTRY}
            for code, info in TYPE_INFO.items()
        ],
    }


def types_for_sector(sector: str) -> List[str]:
    return [code for code, info in TYPE_INFO.items() if sector in info["sectors"]]


def restricted_types() -> List[str]:
    """Types réservés aux administrateurs."""
    return [code for code, info in TYPE_INFO.items() if info["sensitivity"] == "very_high"]


def sensitivity_of(code: Optional[str]) -> str:
    return TYPE_INFO.get(code or "", {}).get("sensitivity", "standard")


def label_of(code: Optional[str]) -> str:
    return TYPE_INFO.get(code or "", {}).get("label", code or "—")


def provider_allowed(code: Optional[str]) -> bool:
    """Si SENSITIVE_PROVIDERS est renseigné, seuls ces fournisseurs d'IA peuvent traiter les types sensibles."""
    allowed = [p.strip().lower() for p in (settings.SENSITIVE_PROVIDERS or "").split(",") if p.strip()]
    if not allowed or sensitivity_of(code) == "standard":
        return True
    return settings.LLM_PROVIDER.lower() in allowed









# from dataclasses import dataclass
# from typing import Callable, Dict, List, Optional, Type

# from pydantic import BaseModel

# from app.schemas.cv import CVData
# from app.schemas.invoice import InvoiceData
# from app.services.pipeline import enrichers, validators

# # Types reconnus par la classification (même ceux qu'on ne sait pas encore extraire)
# CLASSES = ["invoice", "cv", "contract", "id", "other"]


# @dataclass(frozen=True)
# class DocTypeDef:
#     code: str
#     label: str
#     schema: Type[BaseModel]
#     instructions: str
#     validate: Callable[[dict, str], List[dict]]
#     enrich: Optional[Callable[[dict], dict]] = None


# INVOICE = DocTypeDef(
#     code="invoice",
#     label="facture",
#     schema=InvoiceData,
#     instructions=(
#         "Il s'agit d'une facture ou d'un avoir, en français ou en anglais (ou une autre langue). "
#         "Nombres : renvoie toujours un nombre avec point décimal, sans symbole ni séparateur de milliers. "
#         "Déduis le format de la langue du document : 1 234,56 € (français) et 1,234.56 $ (anglais) valent tous deux 1234.56. "
#         "Dates au format AAAA-MM-JJ. Si le format est ambigu (03/04/2025), déduis JJ/MM ou MM/JJ de la langue et du pays "
#         "du document (adresse, devise, mentions). "
#         "currency : code ISO déduit du symbole ou du texte (€ = EUR, $ = USD, £ = GBP), sinon null. "
#         "language : langue principale du document (fr, en...). "
#         "Correspondances : sous-total / subtotal = total_ht ; TVA / VAT / tax / sales tax = total_vat ; "
#         "total TTC / total / amount due / balance due = total_ttc ; "
#         "facturé à / bill to = client ; émis par / from / issued by = fournisseur. "
#         "Taux de TVA en pourcentage (20 pour 20 %). "
#         "Ne recalcule aucun montant : recopie ceux du document. "
#         "Mets document_kind à credit_note pour un avoir (credit note)."
#     ),
#     validate=validators.validate_invoice,
# )

# CV = DocTypeDef(
#     code="cv",
#     label="CV",
#     schema=CVData,
#     instructions=(
#         "Il s'agit d'un CV, en français ou en anglais (ou une autre langue). Extrais uniquement ce qui est écrit. "
#         "Ne renseigne JAMAIS l'âge, la date de naissance, le genre, la nationalité, la situation familiale, les enfants, "
#         "l'état de santé, ni aucune information sur l'origine ou la photo : ces données sont volontairement ignorées, "
#         "y compris dans le résumé et les descriptions. "
#         "location : ville et pays seulement, jamais l'adresse complète. "
#         "email et phone : recopie-les tels qu'écrits. "
#         "Dates au format AAAA-MM (AAAA si le mois est absent). Pour un poste en cours (présent, aujourd'hui, en cours, "
#         "current, present), mets is_current à true et end_date à null. "
#         "skills : uniquement des compétences explicitement écrites ; source skills_section si elles figurent dans une rubrique "
#         "de compétences, sinon experience. N'invente et ne déduis aucune compétence. "
#         "Une entrée par poste, formation, langue et certification, dans l'ordre du document. "
#         "language : langue principale du CV (fr, en...)."
#     ),
#     validate=validators.validate_cv,
#     enrich=enrichers.cv_derived,
# )

# # Ajouter un type = ajouter une définition ici
# REGISTRY: Dict[str, DocTypeDef] = {d.code: d for d in (INVOICE, CV)}
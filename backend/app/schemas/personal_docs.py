from typing import List, Literal, Optional

from pydantic import BaseModel, Field

LANG = "Langue principale du document, code ISO 639-1 (fr, en...)"


class PayslipData(BaseModel):
    language: Optional[str] = Field(None, description=LANG)
    employer_name: Optional[str] = None
    employer_siret: Optional[str] = Field(None, description="SIRET de l'employeur (14 chiffres)")
    employee_first_name: Optional[str] = None
    employee_last_name: Optional[str] = None
    job_title: Optional[str] = Field(None, description="Emploi ou poste indiqué")
    period_start: Optional[str] = Field(None, description="Début de la période de paie, AAAA-MM-JJ")
    period_end: Optional[str] = Field(None, description="Fin de la période de paie, AAAA-MM-JJ")
    pay_date: Optional[str] = Field(None, description="Date de paiement, AAAA-MM-JJ")
    currency: Optional[str] = None
    gross_salary: Optional[float] = Field(None, description="Salaire brut du mois")
    net_before_tax: Optional[float] = Field(None, description="Net à payer avant impôt sur le revenu")
    net_taxable: Optional[float] = Field(None, description="Net imposable du mois")
    income_tax_withheld: Optional[float] = Field(None, description="Impôt sur le revenu prélevé à la source ce mois (0 si aucun)")
    net_paid: Optional[float] = Field(None, description="Net payé au salarié (après impôt)")
    ytd_net_taxable: Optional[float] = Field(None, description="Cumul annuel du net imposable")


class EmploymentContractData(BaseModel):
    language: Optional[str] = Field(None, description=LANG)
    contract_type: Optional[Literal["cdi", "cdd", "interim", "apprenticeship", "internship", "other"]] = None
    employer_name: Optional[str] = None
    employer_siret: Optional[str] = Field(None, description="SIRET de l'employeur (14 chiffres)")
    employee_first_name: Optional[str] = None
    employee_last_name: Optional[str] = None
    job_title: Optional[str] = None
    start_date: Optional[str] = Field(None, description="Date de début, AAAA-MM-JJ")
    end_date: Optional[str] = Field(None, description="Date de fin (CDD, stage...), AAAA-MM-JJ")
    signature_date: Optional[str] = Field(None, description="Date de signature, AAAA-MM-JJ")
    trial_period: Optional[str] = Field(None, description="Période d'essai telle qu'écrite (ex. « 2 mois, renouvelable une fois »)")
    working_hours: Optional[str] = Field(None, description="Durée du travail telle qu'écrite")
    gross_salary: Optional[float] = Field(None, description="Rémunération brute")
    salary_period: Optional[Literal["month", "year", "hour"]] = None
    currency: Optional[str] = None
    collective_agreement: Optional[str] = None
    work_location: Optional[str] = Field(None, description="Ville ou lieu de travail")
    notice_period: Optional[str] = Field(None, description="Préavis tel qu'écrit")
    special_clauses: List[str] = Field(default_factory=list, description="Libellés courts des clauses particulières présentes")


class TaxNoticeData(BaseModel):
    language: Optional[str] = Field(None, description=LANG)
    income_year: Optional[int] = Field(None, description="Année des revenus (« revenus de 2025 »)")
    issue_year: Optional[int] = Field(None, description="Année de l'avis (« avis d'impôt 2026 »)")
    notice_date: Optional[str] = Field(None, description="Date d'établissement, AAAA-MM-JJ")
    declarant_1_name: Optional[str] = None
    declarant_2_name: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    fiscal_reference_income: Optional[float] = Field(None, description="Revenu fiscal de référence")
    household_parts: Optional[float] = Field(None, description="Nombre de parts")
    income_tax_amount: Optional[float] = Field(None, description="Montant de l'impôt sur le revenu net")
    non_taxable: Optional[bool] = Field(None, description="True pour un avis de non-imposition")


class ProofOfAddressData(BaseModel):
    language: Optional[str] = Field(None, description=LANG)
    kind: Literal["utility_bill", "rent_receipt", "property_tax", "hosting_certificate", "home_insurance", "other"] = "other"
    holder_name: Optional[str] = Field(None, description="Personne dont l'adresse est justifiée (l'hébergé pour une attestation d'hébergement)")
    host_name: Optional[str] = Field(None, description="Hébergeant, pour une attestation d'hébergement")
    issuer: Optional[str] = Field(None, description="Émetteur : fournisseur, bailleur, assureur, administration")
    address_line: Optional[str] = Field(None, description="Numéro et rue")
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = Field(None, description="Code pays ISO, par exemple FR")
    issue_date: Optional[str] = Field(None, description="Date du document, AAAA-MM-JJ")
    amount: Optional[float] = Field(None, description="Montant total, s'il y en a un")


class IdentityDocumentData(BaseModel):
    language: Optional[str] = Field(None, description=LANG)
    document_kind: Literal["national_id", "passport", "driving_licence", "residence_permit", "other"] = "other"
    issuing_country: Optional[str] = Field(None, description="Pays émetteur, code ISO")
    last_name: Optional[str] = None
    first_names: Optional[str] = Field(None, description="Prénoms, séparés par des espaces")
    issue_date: Optional[str] = Field(None, description="Date de délivrance, AAAA-MM-JJ")
    expiry_date: Optional[str] = Field(None, description="Date d'expiration, AAAA-MM-JJ")
    mrz_lines: List[str] = Field(default_factory=list, description="Lignes de la zone MRZ, recopiées caractère par caractère (< compris), sinon liste vide")
    mrz_valid: Optional[bool] = Field(None, description="Ne pas renseigner")


class JobDescriptionData(BaseModel):
    language: Optional[str] = Field(None, description=LANG)
    title: Optional[str] = Field(None, description="Intitulé du poste")
    department: Optional[str] = None
    location: Optional[str] = None
    contract_type: Optional[Literal["cdi", "cdd", "interim", "apprenticeship", "internship", "freelance", "other"]] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_period: Optional[Literal["month", "year", "hour"]] = None
    min_years: Optional[float] = Field(None, description="Années d'expérience minimales demandées")
    must_have: List[str] = Field(default_factory=list, description="Compétences, outils ou qualifications indispensables, une par entrée")
    nice_to_have: List[str] = Field(default_factory=list, description="Atouts souhaités mais non indispensables")
    languages: List[str] = Field(default_factory=list, description="Langues exigées")
    summary: Optional[str] = Field(None, description="Résumé des missions en deux ou trois phrases")
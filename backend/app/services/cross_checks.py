import re
import unicodedata
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Document, DocumentStatus

LEGAL = {"sas", "sarl", "sa", "eurl", "sasu", "sci", "snc", "ltd", "inc", "llc", "gmbh", "corp", "co"}


def _fold(s) -> str:
    s = unicodedata.normalize("NFKD", str(s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def norm_id(v) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(v or "").upper())


def supplier_key(d: dict) -> Optional[str]:
    """Identifie un fournisseur : SIREN (via SIRET ou TVA FR) si connu, sinon nom normalisé."""
    siret = re.sub(r"\D", "", str(d.get("supplier_siret") or ""))
    if len(siret) >= 9:
        return "siren:" + siret[:9]
    vat = norm_id(d.get("supplier_vat_number"))
    if vat.startswith("FR") and len(vat) == 13 and vat[4:].isdigit():
        return "siren:" + vat[4:]
    words = [w for w in re.sub(r"[^a-z0-9]+", " ", _fold(d.get("supplier_name"))).split() if w not in LEGAL]
    return "name:" + " ".join(words) if words else None


def invoices_of(db: Session, company_id: int, exclude_id: Optional[int] = None) -> List[Document]:
    q = db.query(Document).filter(
        Document.company_id == company_id, Document.doc_type == "invoice", Document.status == DocumentStatus.DONE
    )
    if exclude_id is not None:
        q = q.filter(Document.id != exclude_id)
    return [d for d in q.all() if isinstance(d.extracted_data, dict)]


def _issue(code: str, message: str, field: str, ref: int) -> dict:
    return {"code": code, "severity": "warning", "message": message, "field": field, "ref_document_id": ref}


def invoice_checks(db: Session, doc: Document, data: dict) -> List[dict]:
    key = supplier_key(data)
    if not key:
        return []
    number, ttc, date, iban = norm_id(data.get("invoice_number")), data.get("total_ttc"), data.get("invoice_date"), norm_id(data.get("iban"))
    issues: List[dict] = []
    ibans = {}
    for other in invoices_of(db, doc.company_id, doc.id):
        od = other.extracted_data
        if supplier_key(od) != key:
            continue
        if number and norm_id(od.get("invoice_number")) == number:
            issues.append(_issue("duplicate_invoice", f"Doublon probable : même fournisseur et même numéro que le document n°{other.id} (« {other.original_filename} »)", "invoice_number", other.id))
        elif ttc is not None and date and od.get("total_ttc") == ttc and od.get("invoice_date") == date:
            issues.append(_issue("possible_duplicate", f"Doublon possible : même fournisseur, même date et même montant que le document n°{other.id} (« {other.original_filename} »)", "invoice_number", other.id))
        if od.get("iban"):
            ibans.setdefault(norm_id(od["iban"]), other.id)
    if iban and ibans and iban not in ibans:
        issues.append(_issue("iban_changed", "IBAN différent de ceux déjà utilisés par ce fournisseur : vérifiez-le avant tout paiement (fraude au changement de RIB possible)", "iban", next(iter(ibans.values()))))
    return issues[:4]


def run(db: Session, doc: Document, data: dict, doc_type: Optional[str]) -> List[dict]:
    return invoice_checks(db, doc, data) if doc_type == "invoice" else []
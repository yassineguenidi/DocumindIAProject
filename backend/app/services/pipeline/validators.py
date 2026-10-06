import re
import unicodedata
from datetime import date
from typing import List, Optional, Tuple

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _num(v) -> Optional[float]:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _close(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol


def _date(s) -> Optional[date]:
    try:
        return date.fromisoformat(s)
    except (TypeError, ValueError):
        return None


def _compact(s) -> str:
    return "".join(ch for ch in str(s or "") if ch.isalnum()).upper()


def _digits(s) -> str:
    return re.sub(r"\D", "", str(s or ""))


def _fold(s) -> str:
    s = unicodedata.normalize("NFKD", str(s or "").lower())
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def parse_ym(v, as_end: bool = False) -> Optional[Tuple[int, int]]:
    """'2021-03' -> (2021, 3). Une année seule vaut janvier (début) ou décembre (fin)."""
    m = re.fullmatch(r"(\d{4})(?:-(\d{2}))?", str(v or "").strip())
    if not m:
        return None
    year = int(m.group(1))
    if m.group(2):
        month = int(m.group(2))
        return (year, month) if 1 <= month <= 12 else None
    return (year, 12 if as_end else 1)


def luhn_ok(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def siret_ok(value) -> bool:
    s = _compact(value)
    if len(s) != 14 or not s.isdigit():
        return False
    if s.startswith("356000000"):  # La Poste : règle particulière
        return sum(int(c) for c in s) % 5 == 0
    return luhn_ok(s)


def vat_ok(value) -> bool:
    s = _compact(value)
    if not s.startswith("FR"):
        return True  # numéros étrangers : non vérifiés ici
    if len(s) != 13 or not s[4:].isdigit():
        return False
    key = s[2:4]
    if not key.isdigit():
        return True
    return int(key) == (12 + 3 * (int(s[4:]) % 97)) % 97


def iban_ok(value) -> bool:
    s = _compact(value)
    if not (15 <= len(s) <= 34) or not s[:2].isalpha() or not s[2:4].isdigit():
        return False
    try:
        n = int("".join(str(int(ch, 36)) for ch in s[4:] + s[:4]))
    except ValueError:
        return False
    return n % 97 == 1


_FIELD_BY_CODE = {
    "ungrounded_number": "invoice_number",
    "total_mismatch": "total_ttc", "negative_total": "total_ttc",
    "bad_invoice_date": "invoice_date", "bad_due_date": "due_date", "due_before_invoice": "due_date",
    "lines_mismatch": "lines", "vat_sum_mismatch": "vat_breakdown", "vat_rate_mismatch": "vat_breakdown",
    "bad_siret": "supplier_siret", "bad_vat_number": "supplier_vat_number", "bad_iban": "iban",
    "missing_name": "first_name", "bad_email": "email", "empty_cv": "experiences",
    "bad_date": "experiences", "end_before_start": "experiences", "future_start": "experiences",
}


def _field_of(code: str) -> Optional[str]:
    if code in _FIELD_BY_CODE:
        return _FIELD_BY_CODE[code]
    for prefix in ("missing_", "ungrounded_"):
        if code.startswith(prefix):
            return code[len(prefix):]
    return None


def _issue(code: str, severity: str, message: str) -> dict:
    # "error" = probable erreur d'extraction (déclenche un second essai avec le modèle puissant)
    # "warning" = point à vérifier par un humain
    return {"code": code, "severity": severity, "message": message, "field": _field_of(code)}


def _amount_in_text(v: float, digits_text: str) -> bool:
    """Le montant (1 234,56 / 1,234.56 / 1234.56) figure-t-il dans le texte ? Compare les chiffres seuls."""
    cents = f"{abs(v):.2f}".replace(".", "")
    return cents in digits_text or (float(v).is_integer() and str(int(abs(v))) in digits_text)


# ---------------------------------------------------------------- factures
def validate_invoice(d: dict, text: str = "") -> List[dict]:
    issues: List[dict] = []

    for field, label in (("supplier_name", "fournisseur"), ("invoice_number", "numéro de facture"),
                         ("invoice_date", "date de facture"), ("total_ttc", "total TTC")):
        if d.get(field) in (None, ""):
            issues.append(_issue(f"missing_{field}", "error", f"Champ manquant : {label}"))

    inv_date, due_date = _date(d.get("invoice_date")), _date(d.get("due_date"))
    if d.get("invoice_date") and inv_date is None:
        issues.append(_issue("bad_invoice_date", "error", "Date de facture invalide"))
    if d.get("due_date") and due_date is None:
        issues.append(_issue("bad_due_date", "error", "Date d'échéance invalide"))
    if inv_date and due_date and due_date < inv_date:
        issues.append(_issue("due_before_invoice", "warning", "Échéance antérieure à la date de facture"))

    ht, vat, ttc = _num(d.get("total_ht")), _num(d.get("total_vat")), _num(d.get("total_ttc"))
    if None not in (ht, vat, ttc) and not _close(ht + vat, ttc, 0.02):
        issues.append(_issue("total_mismatch", "error", "Incohérence : HT + TVA ≠ TTC"))
    if d.get("document_kind") == "invoice" and ttc is not None and ttc < 0:
        issues.append(_issue("negative_total", "warning", "Montant négatif sur une facture (avoir ?)"))

    lines = d.get("lines") or []
    line_totals = [_num(line.get("total_ht")) for line in lines]
    if ht is not None and lines and None not in line_totals:
        if not _close(sum(line_totals), ht, max(0.05, abs(ht) * 0.001)):
            issues.append(_issue("lines_mismatch", "warning", "La somme des lignes ne correspond pas au total HT"))

    breakdown = d.get("vat_breakdown") or []
    amounts = [_num(v.get("amount")) for v in breakdown]
    if vat is not None and breakdown and None not in amounts and not _close(sum(amounts), vat, 0.05):
        issues.append(_issue("vat_sum_mismatch", "error", "La somme des TVA par taux ne correspond pas à la TVA totale"))
    for v in breakdown:
        rate, base, amount = _num(v.get("rate")), _num(v.get("base")), _num(v.get("amount"))
        if None not in (rate, base, amount) and not _close(base * rate / 100, amount, 0.05):
            issues.append(_issue("vat_rate_mismatch", "warning", f"TVA à {rate:g} % : {base} × taux ≠ {amount}"))

    if d.get("supplier_siret") and not siret_ok(d["supplier_siret"]):
        issues.append(_issue("bad_siret", "warning", "SIRET du fournisseur invalide (clé de contrôle)"))
    if d.get("supplier_vat_number") and not vat_ok(d["supplier_vat_number"]):
        issues.append(_issue("bad_vat_number", "warning", "N° de TVA du fournisseur invalide (clé de contrôle)"))
    if d.get("iban") and not iban_ok(d["iban"]):
        issues.append(_issue("bad_iban", "warning", "IBAN invalide (clé de contrôle)"))

    if text:  # ancrage : une valeur absente du texte source est probablement inventée
        if d.get("invoice_number") and _compact(d["invoice_number"]) not in _compact(text):
            issues.append(_issue("ungrounded_number", "warning", "N° de facture introuvable dans le texte (à vérifier)"))
        digits_text = _digits(text)
        for field, label in (("total_ht", "Total HT"), ("total_vat", "TVA"), ("total_ttc", "Total TTC")):
            v = _num(d.get(field))
            if v is not None and not _amount_in_text(v, digits_text):
                issues.append(_issue(f"ungrounded_{field}", "warning", f"{label} introuvable dans le texte (à vérifier)"))

    return issues


# --------------------------------------------------------------------- CV
def validate_cv(d: dict, text: str = "") -> List[dict]:
    issues: List[dict] = []

    if not (d.get("first_name") or d.get("last_name")):
        issues.append(_issue("missing_name", "error", "Nom du candidat introuvable"))
    experiences = d.get("experiences") or []
    if not (experiences or d.get("education") or d.get("skills")):
        issues.append(_issue("empty_cv", "error", "Aucune expérience, formation ni compétence détectée"))
    if d.get("email") and not EMAIL_RE.match(str(d["email"]).strip()):
        issues.append(_issue("bad_email", "warning", "Adresse e-mail invalide"))

    today = (date.today().year, date.today().month)
    for i, e in enumerate(experiences, 1):
        label = e.get("company") or e.get("title") or f"expérience {i}"
        for name, value in (("début", e.get("start_date")), ("fin", e.get("end_date"))):
            if value and parse_ym(value) is None:
                issues.append(_issue("bad_date", "error", f"Date de {name} invalide ({label})"))
        start, end = parse_ym(e.get("start_date")), parse_ym(e.get("end_date"), as_end=True)
        if start and end and end < start:
            issues.append(_issue("end_before_start", "warning", f"Fin antérieure au début ({label})"))
        if start and start > today:
            issues.append(_issue("future_start", "warning", f"Début dans le futur ({label})"))

    if text:  # ancrage
        folded = _fold(text)
        if d.get("email") and str(d["email"]).strip().lower() not in text.lower():
            issues.append(_issue("ungrounded_email", "warning", "E-mail introuvable dans le texte du CV (à vérifier)"))
        phone = _digits(d.get("phone"))
        if len(phone) >= 9 and phone[-9:] not in _digits(text):
            issues.append(_issue("ungrounded_phone", "warning", "Téléphone introuvable dans le texte du CV (à vérifier)"))
        for key, label in (("first_name", "Prénom"), ("last_name", "Nom")):
            if d.get(key) and _fold(d[key]) not in folded:
                issues.append(_issue(f"ungrounded_{key}", "warning", f"{label} introuvable dans le texte du CV (à vérifier)"))

    return issues
"""Contrôles de cohérence par type de document. Code pur : aucune IA, aucune base de données."""
import re
import unicodedata
from datetime import date
from typing import List, Optional, Tuple

from app.services.pipeline import mrz

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ------------------------------------------------------------------ utilitaires
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


def siren_ok(value) -> bool:
    s = _compact(value)
    return len(s) == 9 and s.isdigit() and luhn_ok(s)


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


# Code d'alerte -> champ de l'écran de relecture (les préfixes missing_, ungrounded_ et invalid_ sont automatiques)
_FIELD_BY_CODE = {
    "ungrounded_number": "invoice_number",
    "total_mismatch": "total_ttc", "negative_total": "total_ttc",
    "bad_invoice_date": "invoice_date", "bad_due_date": "due_date", "due_before_invoice": "due_date",
    "lines_mismatch": "lines", "vat_sum_mismatch": "vat_breakdown", "vat_rate_mismatch": "vat_breakdown",
    "bad_siret": "supplier_siret", "bad_vat_number": "supplier_vat_number", "bad_iban": "iban",
    "missing_name": "first_name", "bad_email": "email", "empty_cv": "experiences",
    "bad_date": "experiences", "end_before_start": "experiences", "future_start": "experiences",
    "period_order": "period_end", "period_long": "period_end", "net_above_gross": "net_paid",
    "net_mismatch": "net_paid", "taxable_above_gross": "net_taxable",
    "contract_type_unknown": "contract_type", "cdd_without_end": "end_date", "cdi_with_end": "end_date",
    "end_before_start_contract": "end_date", "parts_unusual": "household_parts", "year_gap": "issue_year",
    "old_notice": "issue_year", "stale_document": "issue_date", "future_document": "issue_date",
    "id_expired": "expiry_date", "id_expiring": "expiry_date", "mrz_invalid": "mrz_valid",
    "mrz_expiry": "expiry_date", "mrz_name": "last_name",
}


def _field_of(code: str) -> Optional[str]:
    if code in _FIELD_BY_CODE:
        return _FIELD_BY_CODE[code]
    for prefix in ("missing_", "ungrounded_", "invalid_"):
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


def _name_in_text(name, folded_text: str) -> bool:
    tokens = [t for t in re.split(r"[^a-z0-9]+", _fold(name)) if len(t) >= 2]
    return bool(tokens) and all(t in folded_text for t in tokens)


def _common(d: dict, text: str, required=(), dates=(), siret=(), siren=(), iban=(), names=(), amounts=(), positives=()) -> List[dict]:
    """Contrôles génériques pilotés par des listes de (champ, libellé)."""
    issues: List[dict] = []
    for field, label in required:
        if d.get(field) in (None, "", []):
            issues.append(_issue(f"missing_{field}", "error", f"Champ manquant : {label}"))
    for field, label in dates:
        if d.get(field) and _date(d[field]) is None:
            issues.append(_issue(f"invalid_{field}", "error", f"Date invalide : {label}"))
    for field, label in siret:
        if d.get(field) and not siret_ok(d[field]):
            issues.append(_issue(f"invalid_{field}", "warning", f"{label} invalide (clé de contrôle)"))
    for field, label in siren:
        if d.get(field) and not siren_ok(d[field]):
            issues.append(_issue(f"invalid_{field}", "warning", f"{label} invalide (clé de contrôle)"))
    for field, label in iban:
        if d.get(field) and not iban_ok(d[field]):
            issues.append(_issue(f"invalid_{field}", "warning", f"{label} invalide (clé de contrôle)"))
    for field, label in positives:
        v = _num(d.get(field))
        if v is not None and v <= 0:
            issues.append(_issue(f"invalid_{field}", "warning", f"{label} nul ou négatif"))
    if text:  # ancrage : une valeur absente du texte source est probablement inventée
        folded, digits_text = _fold(text), _digits(text)
        for field, label in names:
            values = d.get(field)
            values = values if isinstance(values, list) else [values]
            if any(v and not _name_in_text(v, folded) for v in values):
                issues.append(_issue(f"ungrounded_{field}", "warning", f"{label} introuvable dans le texte (à vérifier)"))
        for field, label in amounts:
            v = _num(d.get(field))
            if v is not None and not _amount_in_text(v, digits_text):
                issues.append(_issue(f"ungrounded_{field}", "warning", f"{label} introuvable dans le texte (à vérifier)"))
    return issues


# ---------------------------------------------------------------------- factures
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

    if text:
        if d.get("invoice_number") and _compact(d["invoice_number"]) not in _compact(text):
            issues.append(_issue("ungrounded_number", "warning", "N° de facture introuvable dans le texte (à vérifier)"))
        digits_text = _digits(text)
        for field, label in (("total_ht", "Total HT"), ("total_vat", "TVA"), ("total_ttc", "Total TTC")):
            v = _num(d.get(field))
            if v is not None and not _amount_in_text(v, digits_text):
                issues.append(_issue(f"ungrounded_{field}", "warning", f"{label} introuvable dans le texte (à vérifier)"))
    return issues


# --------------------------------------------------------------------------- CV
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

    if text:
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


# ------------------------------------------------------------------ bulletin de paie
def validate_payslip(d: dict, text: str = "") -> List[dict]:
    issues = _common(
        d, text,
        required=(("employer_name", "employeur"), ("employee_last_name", "nom du salarié"), ("period_end", "fin de période"),
                  ("gross_salary", "salaire brut"), ("net_paid", "net payé")),
        dates=(("period_start", "début de période"), ("period_end", "fin de période"), ("pay_date", "date de paiement")),
        siret=(("employer_siret", "SIRET de l'employeur"),),
        names=(("employer_name", "Employeur"), ("employee_last_name", "Nom du salarié")),
        amounts=(("gross_salary", "Salaire brut"), ("net_paid", "Net payé")),
        positives=(("gross_salary", "Salaire brut"),),
    )
    start, end = _date(d.get("period_start")), _date(d.get("period_end"))
    if start and end and end < start:
        issues.append(_issue("period_order", "error", "Période de paie : la fin précède le début"))
    elif start and end and (end - start).days > 35:
        issues.append(_issue("period_long", "warning", "Période de paie supérieure à un mois"))
    gross, net, net_bt, tax, taxable = (_num(d.get(k)) for k in ("gross_salary", "net_paid", "net_before_tax", "income_tax_withheld", "net_taxable"))
    if gross is not None and net is not None and net > gross + 0.01:
        issues.append(_issue("net_above_gross", "warning", "Net payé supérieur au salaire brut"))
    if None not in (net_bt, tax, net) and not _close(net_bt - tax, net, 0.05):
        issues.append(_issue("net_mismatch", "warning", "Incohérence : net avant impôt − prélèvement à la source ≠ net payé"))
    if gross is not None and taxable is not None and taxable > gross + 0.01:
        issues.append(_issue("taxable_above_gross", "warning", "Net imposable supérieur au salaire brut"))
    return issues


# --------------------------------------------------------------- contrat de travail
def validate_employment_contract(d: dict, text: str = "") -> List[dict]:
    issues = _common(
        d, text,
        required=(("employer_name", "employeur"), ("employee_last_name", "nom du salarié"), ("start_date", "date de début")),
        dates=(("start_date", "début"), ("end_date", "fin"), ("signature_date", "signature")),
        siret=(("employer_siret", "SIRET de l'employeur"),),
        names=(("employer_name", "Employeur"), ("employee_last_name", "Nom du salarié")),
        amounts=(("gross_salary", "Rémunération"),),
        positives=(("gross_salary", "Rémunération"),),
    )
    kind, start, end = d.get("contract_type"), _date(d.get("start_date")), _date(d.get("end_date"))
    if not kind:
        issues.append(_issue("contract_type_unknown", "warning", "Type de contrat non identifié"))
    if kind == "cdd" and not d.get("end_date"):
        issues.append(_issue("cdd_without_end", "warning", "CDD sans date de fin (terme imprécis ?)"))
    if kind == "cdi" and d.get("end_date"):
        issues.append(_issue("cdi_with_end", "warning", "CDI avec une date de fin"))
    if start and end and end < start:
        issues.append(_issue("end_before_start_contract", "error", "La fin du contrat précède son début"))
    return issues


# ------------------------------------------------------------------- avis d'imposition
def validate_tax_notice(d: dict, text: str = "") -> List[dict]:
    issues = _common(
        d, text,
        required=(("income_year", "année des revenus"), ("fiscal_reference_income", "revenu fiscal de référence")),
        dates=(("notice_date", "date d'établissement"),),
        names=(("declarant_1_name", "Déclarant"),),
        amounts=(("fiscal_reference_income", "Revenu fiscal de référence"),),
    )
    parts, rfr = _num(d.get("household_parts")), _num(d.get("fiscal_reference_income"))
    if parts is not None and (parts <= 0 or (parts * 4) % 1 != 0):
        issues.append(_issue("parts_unusual", "warning", "Nombre de parts inhabituel (multiple de 0,25 attendu)"))
    if rfr is not None and rfr < 0:
        issues.append(_issue("invalid_fiscal_reference_income", "warning", "Revenu fiscal de référence négatif"))
    iy, ey = d.get("income_year"), d.get("issue_year")
    if isinstance(iy, int) and isinstance(ey, int) and ey != iy + 1:
        issues.append(_issue("year_gap", "warning", "L'année de l'avis n'est pas celle qui suit l'année des revenus"))
    today = date.today()
    if isinstance(ey, int) and ey < today.year - (1 if today.month < 9 else 0):
        issues.append(_issue("old_notice", "warning", f"Avis de {ey} : un avis plus récent existe probablement"))
    return issues


# --------------------------------------------------------------- justificatif de domicile
def validate_proof_of_address(d: dict, text: str = "") -> List[dict]:
    issues = _common(
        d, text,
        required=(("holder_name", "titulaire"), ("city", "ville")),
        dates=(("issue_date", "date du document"),),
        names=(("holder_name", "Titulaire"),),
    )
    issued = _date(d.get("issue_date"))
    if not d.get("issue_date"):
        issues.append(_issue("missing_issue_date", "warning", "Date du document introuvable"))
    if issued:
        age = (date.today() - issued).days
        if age < 0:
            issues.append(_issue("future_document", "warning", "Document daté dans le futur"))
        elif d.get("kind") in ("utility_bill", "home_insurance") and age > 92:
            issues.append(_issue("stale_document", "warning", "Justificatif de plus de 3 mois"))
    country = (d.get("country") or "FR").upper()
    if d.get("postal_code") and country == "FR" and not re.fullmatch(r"\d{5}", str(d["postal_code"]).strip()):
        issues.append(_issue("invalid_postal_code", "warning", "Code postal invalide"))
    return issues


# ------------------------------------------------------------------ pièce d'identité
def validate_id(d: dict, text: str = "") -> List[dict]:
    issues = _common(
        d, text,
        required=(("last_name", "nom"),),
        dates=(("expiry_date", "date d'expiration"), ("issue_date", "date de délivrance")),
        names=(("last_name", "Nom"),),
    )
    expiry = _date(d.get("expiry_date"))
    if not d.get("expiry_date"):
        issues.append(_issue("missing_expiry_date", "warning", "Date d'expiration introuvable"))
    elif expiry:
        left = (expiry - date.today()).days
        if left < 0:
            issues.append(_issue("id_expired", "error", "Pièce d'identité expirée"))
        elif left <= 90:
            issues.append(_issue("id_expiring", "warning", f"Pièce d'identité expirant dans {left} jours"))

    lines = d.get("mrz_lines") or []
    parsed = mrz.parse(lines) if lines else None
    if parsed is not None:
        if not mrz.is_valid(parsed):
            bad = ", ".join(k for k, ok in parsed["checks"].items() if not ok)
            issues.append(_issue("mrz_invalid", "error", f"Zone MRZ : clés de contrôle invalides ({bad}), lecture à vérifier"))
        elif expiry and parsed["expiry"] and parsed["expiry"] != d.get("expiry_date"):
            issues.append(_issue("mrz_expiry", "warning", "La date d'expiration diffère de celle de la zone MRZ"))
        if parsed["surname"] and d.get("last_name") and not (set(_fold(parsed["surname"]).split()) & set(_fold(d["last_name"]).replace("-", " ").split())):
            issues.append(_issue("mrz_name", "warning", "Le nom diffère de celui de la zone MRZ"))
    elif d.get("mrz_valid") is False and not lines:
        issues.append(_issue("mrz_invalid", "error", "Zone MRZ : clés de contrôle invalides à la lecture, à vérifier"))
    return issues


def finalize_id(d: dict) -> None:
    """Après lecture : conserve seulement le résultat du contrôle MRZ, jamais les lignes (elles contiennent le n° du document)."""
    lines = d.get("mrz_lines") or []
    parsed = mrz.parse(lines) if lines else None
    if parsed is not None:
        d["mrz_valid"] = mrz.is_valid(parsed)
        if not d.get("expiry_date") and d["mrz_valid"] and parsed["expiry"]:
            d["expiry_date"] = parsed["expiry"]
    d["mrz_lines"] = []


# ------------------------------------------------------------------------------ RH
def validate_job_description(d: dict, text: str = "") -> List[dict]:
    issues = _common(d, text, required=(("title", "intitulé du poste"),))
    if not d.get("must_have"):
        issues.append(_issue("missing_must_have", "warning", "Aucun critère indispensable détecté"))
    my = _num(d.get("min_years"))
    if my is not None and my < 0:
        issues.append(_issue("invalid_min_years", "warning", "Expérience minimale négative"))
    lo, hi = _num(d.get("salary_min")), _num(d.get("salary_max"))
    if lo is not None and hi is not None and lo > hi:
        issues.append(_issue("invalid_salary_min", "warning", "Salaire minimum supérieur au maximum"))
    return issues




# import re
# import unicodedata
# from datetime import date
# from typing import List, Optional, Tuple

# EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# def _num(v) -> Optional[float]:
#     return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


# def _close(a: float, b: float, tol: float) -> bool:
#     return abs(a - b) <= tol


# def _date(s) -> Optional[date]:
#     try:
#         return date.fromisoformat(s)
#     except (TypeError, ValueError):
#         return None


# def _compact(s) -> str:
#     return "".join(ch for ch in str(s or "") if ch.isalnum()).upper()


# def _digits(s) -> str:
#     return re.sub(r"\D", "", str(s or ""))


# def _fold(s) -> str:
#     s = unicodedata.normalize("NFKD", str(s or "").lower())
#     return "".join(ch for ch in s if not unicodedata.combining(ch))


# def parse_ym(v, as_end: bool = False) -> Optional[Tuple[int, int]]:
#     """'2021-03' -> (2021, 3). Une année seule vaut janvier (début) ou décembre (fin)."""
#     m = re.fullmatch(r"(\d{4})(?:-(\d{2}))?", str(v or "").strip())
#     if not m:
#         return None
#     year = int(m.group(1))
#     if m.group(2):
#         month = int(m.group(2))
#         return (year, month) if 1 <= month <= 12 else None
#     return (year, 12 if as_end else 1)


# def luhn_ok(digits: str) -> bool:
#     total = 0
#     for i, ch in enumerate(reversed(digits)):
#         d = int(ch)
#         if i % 2 == 1:
#             d *= 2
#             if d > 9:
#                 d -= 9
#         total += d
#     return total % 10 == 0


# def siret_ok(value) -> bool:
#     s = _compact(value)
#     if len(s) != 14 or not s.isdigit():
#         return False
#     if s.startswith("356000000"):  # La Poste : règle particulière
#         return sum(int(c) for c in s) % 5 == 0
#     return luhn_ok(s)


# def vat_ok(value) -> bool:
#     s = _compact(value)
#     if not s.startswith("FR"):
#         return True  # numéros étrangers : non vérifiés ici
#     if len(s) != 13 or not s[4:].isdigit():
#         return False
#     key = s[2:4]
#     if not key.isdigit():
#         return True
#     return int(key) == (12 + 3 * (int(s[4:]) % 97)) % 97


# def iban_ok(value) -> bool:
#     s = _compact(value)
#     if not (15 <= len(s) <= 34) or not s[:2].isalpha() or not s[2:4].isdigit():
#         return False
#     try:
#         n = int("".join(str(int(ch, 36)) for ch in s[4:] + s[:4]))
#     except ValueError:
#         return False
#     return n % 97 == 1


# _FIELD_BY_CODE = {
#     "ungrounded_number": "invoice_number",
#     "total_mismatch": "total_ttc", "negative_total": "total_ttc",
#     "bad_invoice_date": "invoice_date", "bad_due_date": "due_date", "due_before_invoice": "due_date",
#     "lines_mismatch": "lines", "vat_sum_mismatch": "vat_breakdown", "vat_rate_mismatch": "vat_breakdown",
#     "bad_siret": "supplier_siret", "bad_vat_number": "supplier_vat_number", "bad_iban": "iban",
#     "missing_name": "first_name", "bad_email": "email", "empty_cv": "experiences",
#     "bad_date": "experiences", "end_before_start": "experiences", "future_start": "experiences",
# }


# def _field_of(code: str) -> Optional[str]:
#     if code in _FIELD_BY_CODE:
#         return _FIELD_BY_CODE[code]
#     for prefix in ("missing_", "ungrounded_"):
#         if code.startswith(prefix):
#             return code[len(prefix):]
#     return None


# def _issue(code: str, severity: str, message: str) -> dict:
#     # "error" = probable erreur d'extraction (déclenche un second essai avec le modèle puissant)
#     # "warning" = point à vérifier par un humain
#     return {"code": code, "severity": severity, "message": message, "field": _field_of(code)}


# def _amount_in_text(v: float, digits_text: str) -> bool:
#     """Le montant (1 234,56 / 1,234.56 / 1234.56) figure-t-il dans le texte ? Compare les chiffres seuls."""
#     cents = f"{abs(v):.2f}".replace(".", "")
#     return cents in digits_text or (float(v).is_integer() and str(int(abs(v))) in digits_text)


# # ---------------------------------------------------------------- factures
# def validate_invoice(d: dict, text: str = "") -> List[dict]:
#     issues: List[dict] = []

#     for field, label in (("supplier_name", "fournisseur"), ("invoice_number", "numéro de facture"),
#                          ("invoice_date", "date de facture"), ("total_ttc", "total TTC")):
#         if d.get(field) in (None, ""):
#             issues.append(_issue(f"missing_{field}", "error", f"Champ manquant : {label}"))

#     inv_date, due_date = _date(d.get("invoice_date")), _date(d.get("due_date"))
#     if d.get("invoice_date") and inv_date is None:
#         issues.append(_issue("bad_invoice_date", "error", "Date de facture invalide"))
#     if d.get("due_date") and due_date is None:
#         issues.append(_issue("bad_due_date", "error", "Date d'échéance invalide"))
#     if inv_date and due_date and due_date < inv_date:
#         issues.append(_issue("due_before_invoice", "warning", "Échéance antérieure à la date de facture"))

#     ht, vat, ttc = _num(d.get("total_ht")), _num(d.get("total_vat")), _num(d.get("total_ttc"))
#     if None not in (ht, vat, ttc) and not _close(ht + vat, ttc, 0.02):
#         issues.append(_issue("total_mismatch", "error", "Incohérence : HT + TVA ≠ TTC"))
#     if d.get("document_kind") == "invoice" and ttc is not None and ttc < 0:
#         issues.append(_issue("negative_total", "warning", "Montant négatif sur une facture (avoir ?)"))

#     lines = d.get("lines") or []
#     line_totals = [_num(line.get("total_ht")) for line in lines]
#     if ht is not None and lines and None not in line_totals:
#         if not _close(sum(line_totals), ht, max(0.05, abs(ht) * 0.001)):
#             issues.append(_issue("lines_mismatch", "warning", "La somme des lignes ne correspond pas au total HT"))

#     breakdown = d.get("vat_breakdown") or []
#     amounts = [_num(v.get("amount")) for v in breakdown]
#     if vat is not None and breakdown and None not in amounts and not _close(sum(amounts), vat, 0.05):
#         issues.append(_issue("vat_sum_mismatch", "error", "La somme des TVA par taux ne correspond pas à la TVA totale"))
#     for v in breakdown:
#         rate, base, amount = _num(v.get("rate")), _num(v.get("base")), _num(v.get("amount"))
#         if None not in (rate, base, amount) and not _close(base * rate / 100, amount, 0.05):
#             issues.append(_issue("vat_rate_mismatch", "warning", f"TVA à {rate:g} % : {base} × taux ≠ {amount}"))

#     if d.get("supplier_siret") and not siret_ok(d["supplier_siret"]):
#         issues.append(_issue("bad_siret", "warning", "SIRET du fournisseur invalide (clé de contrôle)"))
#     if d.get("supplier_vat_number") and not vat_ok(d["supplier_vat_number"]):
#         issues.append(_issue("bad_vat_number", "warning", "N° de TVA du fournisseur invalide (clé de contrôle)"))
#     if d.get("iban") and not iban_ok(d["iban"]):
#         issues.append(_issue("bad_iban", "warning", "IBAN invalide (clé de contrôle)"))

#     if text:  # ancrage : une valeur absente du texte source est probablement inventée
#         if d.get("invoice_number") and _compact(d["invoice_number"]) not in _compact(text):
#             issues.append(_issue("ungrounded_number", "warning", "N° de facture introuvable dans le texte (à vérifier)"))
#         digits_text = _digits(text)
#         for field, label in (("total_ht", "Total HT"), ("total_vat", "TVA"), ("total_ttc", "Total TTC")):
#             v = _num(d.get(field))
#             if v is not None and not _amount_in_text(v, digits_text):
#                 issues.append(_issue(f"ungrounded_{field}", "warning", f"{label} introuvable dans le texte (à vérifier)"))

#     return issues


# # --------------------------------------------------------------------- CV
# def validate_cv(d: dict, text: str = "") -> List[dict]:
#     issues: List[dict] = []

#     if not (d.get("first_name") or d.get("last_name")):
#         issues.append(_issue("missing_name", "error", "Nom du candidat introuvable"))
#     experiences = d.get("experiences") or []
#     if not (experiences or d.get("education") or d.get("skills")):
#         issues.append(_issue("empty_cv", "error", "Aucune expérience, formation ni compétence détectée"))
#     if d.get("email") and not EMAIL_RE.match(str(d["email"]).strip()):
#         issues.append(_issue("bad_email", "warning", "Adresse e-mail invalide"))

#     today = (date.today().year, date.today().month)
#     for i, e in enumerate(experiences, 1):
#         label = e.get("company") or e.get("title") or f"expérience {i}"
#         for name, value in (("début", e.get("start_date")), ("fin", e.get("end_date"))):
#             if value and parse_ym(value) is None:
#                 issues.append(_issue("bad_date", "error", f"Date de {name} invalide ({label})"))
#         start, end = parse_ym(e.get("start_date")), parse_ym(e.get("end_date"), as_end=True)
#         if start and end and end < start:
#             issues.append(_issue("end_before_start", "warning", f"Fin antérieure au début ({label})"))
#         if start and start > today:
#             issues.append(_issue("future_start", "warning", f"Début dans le futur ({label})"))

#     if text:  # ancrage
#         folded = _fold(text)
#         if d.get("email") and str(d["email"]).strip().lower() not in text.lower():
#             issues.append(_issue("ungrounded_email", "warning", "E-mail introuvable dans le texte du CV (à vérifier)"))
#         phone = _digits(d.get("phone"))
#         if len(phone) >= 9 and phone[-9:] not in _digits(text):
#             issues.append(_issue("ungrounded_phone", "warning", "Téléphone introuvable dans le texte du CV (à vérifier)"))
#         for key, label in (("first_name", "Prénom"), ("last_name", "Nom")):
#             if d.get(key) and _fold(d[key]) not in folded:
#                 issues.append(_issue(f"ungrounded_{key}", "warning", f"{label} introuvable dans le texte du CV (à vérifier)"))

#     return issues
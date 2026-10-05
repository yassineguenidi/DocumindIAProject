from datetime import date
from typing import List, Optional


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


def _issue(code: str, severity: str, message: str) -> dict:
    # "error" = probable erreur d'extraction (déclenche un second essai avec le modèle puissant)
    # "warning" = point à vérifier par un humain
    return {"code": code, "severity": severity, "message": message}


def validate_invoice(d: dict) -> List[dict]:
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

    return issues
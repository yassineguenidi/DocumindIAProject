"""Lecture et contrôle de la zone MRZ (passeports, cartes d'identité au format TD1, TD2 et TD3).
Les clés de contrôle permettent de détecter une mauvaise lecture sans stocker le numéro du document."""
import re
from datetime import date
from typing import List, Optional

WEIGHTS = (7, 3, 1)


def _val(ch: str) -> int:
    if ch.isdigit():
        return int(ch)
    if "A" <= ch <= "Z":
        return ord(ch) - 55
    return 0  # « < »


def check_digit(s: str) -> str:
    return str(sum(_val(c) * WEIGHTS[i % 3] for i, c in enumerate(s)) % 10)


def _ok(field: str, digit: str) -> bool:
    return len(digit) == 1 and digit.isdigit() and check_digit(field) == digit


def _iso(yymmdd: str, century: Optional[int] = 2000) -> Optional[str]:
    if not re.fullmatch(r"\d{6}", yymmdd):
        return None
    yy, mm, dd = int(yymmdd[:2]), int(yymmdd[2:4]), int(yymmdd[4:])
    try:
        return date(century + yy, mm, dd).isoformat()
    except ValueError:
        return None


def _names(raw: str):
    parts = raw.split("<<", 1)
    surname = parts[0].replace("<", " ").strip()
    given = parts[1].replace("<", " ").strip() if len(parts) > 1 else ""
    return surname, given


def parse(lines: List[str]) -> Optional[dict]:
    """Retourne None si le format n'est pas reconnu, sinon le détail des contrôles."""
    ls = [re.sub(r"\s+", "", str(x)).upper() for x in lines if str(x).strip()]
    if len(ls) == 2 and all(len(x) == 44 for x in ls):  # passeport (TD3)
        l1, l2 = ls
        checks = {
            "document": _ok(l2[0:9], l2[9]),
            "birth": _ok(l2[13:19], l2[19]),
            "expiry": _ok(l2[21:27], l2[27]),
            "composite": _ok(l2[0:10] + l2[13:20] + l2[21:43], l2[43]),
        }
        surname, given = _names(l1[5:44])
        return {"format": "TD3", "checks": checks, "expiry": _iso(l2[21:27]), "surname": surname, "given": given}
    if len(ls) == 3 and all(len(x) == 30 for x in ls):  # carte d'identité (TD1)
        l1, l2, l3 = ls
        checks = {
            "document": _ok(l1[5:14], l1[14]),
            "birth": _ok(l2[0:6], l2[6]),
            "expiry": _ok(l2[8:14], l2[14]),
            "composite": _ok(l1[5:30] + l2[0:7] + l2[8:15] + l2[18:29], l2[29]),
        }
        surname, given = _names(l3)
        return {"format": "TD1", "checks": checks, "expiry": _iso(l2[8:14]), "surname": surname, "given": given}
    if len(ls) == 2 and all(len(x) == 36 for x in ls):  # TD2
        l1, l2 = ls
        checks = {
            "document": _ok(l2[0:9], l2[9]),
            "birth": _ok(l2[13:19], l2[19]),
            "expiry": _ok(l2[21:27], l2[27]),
            "composite": _ok(l2[0:10] + l2[13:20] + l2[21:35], l2[35]),
        }
        surname, given = _names(l1[5:36])
        return {"format": "TD2", "checks": checks, "expiry": _iso(l2[21:27]), "surname": surname, "given": given}
    return None


def is_valid(parsed: dict) -> bool:
    return all(parsed["checks"].values())
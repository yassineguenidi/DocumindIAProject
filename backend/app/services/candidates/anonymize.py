import copy
import re
from typing import Iterable, List, Optional

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
URL = re.compile(r"(?:https?://|www\.)\S+|(?:linkedin|github)\.com/\S+", re.I)
PHONE = re.compile(r"(?<!\w)\+?\d[\d .()-]{7,}\d(?!\w)")
MASK = "[masqué]"


def display_name(doc_id: int, data: dict, anonymous: bool) -> str:
    if not anonymous:
        name = " ".join(x for x in (data.get("first_name"), data.get("last_name")) if x)
        if name:
            return name
    return f"Candidat n°{doc_id}"


def name_parts(data: dict) -> List[str]:
    parts: List[str] = []
    for key in ("first_name", "last_name"):
        value = data.get(key) or ""
        parts += [value, *re.split(r"[\s-]+", value)]
    return [p for p in dict.fromkeys(parts) if len(p) >= 2]


def scrub_text(text: Optional[str], names: Iterable[str]) -> Optional[str]:
    """Masque e-mails, liens, téléphones (9 chiffres ou plus) et prénom/nom dans un texte libre."""
    if not text:
        return text
    out = URL.sub(MASK, EMAIL.sub(MASK, text))
    out = PHONE.sub(lambda m: MASK if len(re.sub(r"\D", "", m.group())) >= 9 else m.group(), out)
    for n in names:
        out = re.sub(rf"(?<!\w){re.escape(n)}(?!\w)", MASK, out, flags=re.I)
    return out


def anonymize_cv(data: dict, doc_id: int) -> dict:
    d = copy.deepcopy(data)
    names = name_parts(data)
    d["first_name"], d["last_name"] = f"Candidat n°{doc_id}", None
    d["email"] = d["phone"] = None
    d["links"] = []
    for key in ("headline", "summary"):
        d[key] = scrub_text(d.get(key), names)
    for e in d.get("experiences") or []:
        e["description"] = scrub_text(e.get("description"), names)
    return d
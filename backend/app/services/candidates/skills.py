import re
import unicodedata
from typing import List

# canonique -> synonymes (minuscules, sans accents). Ajouter une ligne enrichit toute la recherche.
ALIASES = {
    "JavaScript": ["javascript", "js", "ecmascript"],
    "TypeScript": ["typescript"],
    "Node.js": ["node.js", "nodejs"],
    "React": ["react", "reactjs", "react.js"],
    "C++": ["c++", "cpp"],
    "C#": ["c#", "csharp"],
    "PostgreSQL": ["postgresql", "postgres"],
    "Kubernetes": ["kubernetes", "k8s"],
    "CI/CD": ["ci/cd", "cicd", "integration continue"],
    "Machine Learning": ["machine learning", "ml", "apprentissage automatique"],
    "Deep Learning": ["deep learning", "apprentissage profond"],
    "NLP": ["nlp", "traitement du langage naturel", "natural language processing"],
    "Computer Vision": ["computer vision", "vision par ordinateur"],
    "Scikit-learn": ["scikit-learn", "scikit learn", "sklearn"],
    "PyTorch": ["pytorch"],
    "TensorFlow": ["tensorflow"],
    "Power BI": ["power bi", "powerbi"],
    "Excel": ["excel", "microsoft excel", "ms excel"],
    "Data Analysis": ["data analysis", "data analytics", "analyse de donnees"],
    "Gestion de projet": ["gestion de projet", "project management", "pilotage de projet"],
    "Comptabilité": ["comptabilite", "accounting"],
    "Paie": ["paie", "payroll", "gestion de la paie"],
    "Recrutement": ["recrutement", "recruitment", "recruiting", "talent acquisition"],
    "Marketing digital": ["marketing digital", "digital marketing"],
    "Agile": ["agile", "methodes agiles", "agile methodologies"],
}


def fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", (s or "").lower().replace("’", "'"))
    return "".join(c for c in s if not unicodedata.combining(c))


def tokens(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+(?:[+#]+)?", fold(text))


_ALIAS_TO_CANON = {fold(a): canon for canon, al in ALIASES.items() for a in [canon, *al]}


def canonical(name: str) -> str:
    name = (name or "").strip()
    return _ALIAS_TO_CANON.get(fold(name), name)


def aliases_of(skill: str) -> List[str]:
    canon = canonical(skill)
    return list({fold(canon), fold(skill), *ALIASES.get(canon, [])})


def mentioned(skill: str, folded_text: str) -> bool:
    """La compétence (ou un synonyme) figure-t-elle dans le texte ? Recherche par mot entier."""
    return any(
        re.search(rf"(?<![a-z0-9]){re.escape(a)}(?![a-z0-9])", folded_text) for a in aliases_of(skill) if a
    )
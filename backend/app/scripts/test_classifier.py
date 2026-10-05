from app.services.pipeline.classifier import _by_rules

CASES = [
    ("Facture N° 2025-014. Montant HT 100 €, TVA 20 €, Total TTC 120 €. Échéance : 30 jours.", "invoice"),
    ("INVOICE No 88. Bill to: ACME. Subtotal $100, Sales tax $8, Total due $108. Due date: 05/12/2025.", "invoice"),
    ("Curriculum Vitae. Expérience professionnelle : ingénieur. Compétences : Python. Formation : Master.", "cv"),
    ("RESUME. Work experience: data analyst. Skills: SQL, Python. Education: BSc. Languages: English.", "cv"),
    ("Contrat de travail entre les soussignés. Article 1 : objet. Clause de résiliation.", "contract"),
    ("Our innovation team reviews the syntax of your code.", None),  # pas de faux positif (« vat », « tax »)
    ("Hello, comment allez-vous ?", None),
]

ok = 0
for text, expected in CASES:
    got = _by_rules(text)
    status = "OK " if got == expected else "ERR"
    ok += got == expected
    print(f"{status} attendu={expected!s:9} obtenu={got!s:9} | {text[:60]}")
print(f"\n{ok}/{len(CASES)} cas réussis")
import json
import sys
from pathlib import Path

from app.services.pipeline import classifier, extractor, reader
from app.services.pipeline.errors import PipelineError
from app.services.pipeline.registry import REGISTRY

MIMES = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage : python -m app.scripts.run_pipeline "chemin\\vers\\fichier.pdf"')
        return
    path = Path(sys.argv[1])
    mime = MIMES.get(path.suffix.lower())
    if not path.exists() or not mime:
        print("Fichier introuvable ou format non pris en charge (PDF, PNG, JPG)")
        return
    try:
        doc = reader.read_document(path, mime)
        print(f"Lecture : mode={doc.mode}, pages={doc.pages}, texte={len(doc.text)} caractères")
        doc_type, cls = classifier.classify(doc)
        print(f"Type détecté : {doc_type}" + (" (par IA)" if cls else " (par règles)"))
        defn = REGISTRY.get(doc_type)
        if defn is None:
            print("Extraction pas encore disponible pour ce type.")
            return
        ext = extractor.extract(defn, doc)
    except PipelineError as exc:
        print("Erreur :", exc)
        return
    print(json.dumps(ext.data, indent=2, ensure_ascii=False))
    print("\nContrôles :", "aucun problème" if not ext.issues else "")
    for i in ext.issues:
        print(f"  [{i['severity']}] {i['message']}")
    print("Méta :", ext.meta)


if __name__ == "__main__":
    main()
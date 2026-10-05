"""Évaluation du pipeline sur un jeu de test.

  python -m app.scripts.evaluate run --name gemini-lite
  python -m app.scripts.evaluate init-truth --name gemini-lite
  python -m app.scripts.evaluate score --name gemini-lite [-v]
  python -m app.scripts.evaluate compare gemini-lite gemini-flash
"""
import argparse
import json
import re
import time
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.services.pipeline import classifier, extractor, reader
from app.services.pipeline.errors import PipelineError
from app.services.pipeline.registry import REGISTRY

BASE = Path(__file__).resolve().parents[2] / "eval"
CASES, TRUTH, RUNS = BASE / "cases", BASE / "truth", BASE / "runs"
MIMES = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}

SCALARS = [
    "document_kind", "language", "supplier_name", "supplier_siret", "supplier_vat_number",
    "customer_name", "invoice_number", "invoice_date", "due_date", "currency",
    "total_ht", "total_vat", "total_ttc", "iban",
]
NUMERIC = {"total_ht", "total_vat", "total_ttc"}
IDLIKE = {"supplier_siret", "supplier_vat_number", "iban", "invoice_number"}
EXACT_STR = {"invoice_date", "due_date", "document_kind", "language", "currency"}
LEGAL_FORMS = {"sas", "sarl", "sa", "eurl", "sasu", "ltd", "inc", "llc", "gmbh", "corp"}


# ---------- Comparaison des valeurs ----------
def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def _norm_text(v) -> str:
    words = re.sub(r"[^a-z0-9]+", " ", _fold(str(v))).split()
    return " ".join(w for w in words if w not in LEGAL_FORMS)


def _norm_id(v) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(v).upper())


def _empty(v) -> bool:
    return v is None or v == ""


def field_ok(field: str, expected, got) -> bool:
    if _empty(expected):
        return _empty(got)
    if _empty(got):
        return False
    try:
        if field in NUMERIC:
            return abs(float(expected) - float(got)) <= 0.01
        if field in IDLIKE:
            return _norm_id(expected) == _norm_id(got)
        if field in EXACT_STR:
            return str(expected).strip().lower() == str(got).strip().lower()
        return _norm_text(expected) == _norm_text(got)
    except (TypeError, ValueError):
        return False


def _same_numbers(e: list, g: list) -> bool:
    return len(e) == len(g) and all(abs(a - b) <= 0.01 for a, b in zip(e, g))


def lines_ok(expected, got) -> bool:
    def totals(items):
        return sorted(float(i["total_ht"]) for i in (items or []) if i.get("total_ht") is not None)
    try:
        return _same_numbers(totals(expected), totals(got))
    except (TypeError, ValueError):
        return False


def vat_ok(expected, got) -> bool:
    def pairs(items):
        return sorted((float(i.get("rate") or 0), float(i.get("amount") or 0)) for i in (items or []))
    try:
        e, g = pairs(expected), pairs(got)
    except (TypeError, ValueError):
        return False
    return len(e) == len(g) and all(abs(a[0] - b[0]) <= 0.01 and abs(a[1] - b[1]) <= 0.01 for a, b in zip(e, g))


def check_case(truth: dict, res: dict):
    """Retourne (résultat par champ, liste des erreurs)."""
    data = res.get("data") or {}
    outcomes, wrong = {}, []

    def record(name, ok, exp, got):
        outcomes[name] = ok
        if not ok:
            wrong.append((name, exp, got))

    failed = not res.get("ok", True)
    for f in SCALARS:
        if f in truth:
            record(f, False if failed else field_ok(f, truth[f], data.get(f)), truth[f], data.get(f))
    if "lines" in truth:
        record("lines", False if failed else lines_ok(truth["lines"], data.get("lines")),
               [l.get("total_ht") for l in truth["lines"]], [l.get("total_ht") for l in data.get("lines") or []])
    if "vat_breakdown" in truth:
        record("vat_breakdown", False if failed else vat_ok(truth["vat_breakdown"], data.get("vat_breakdown")),
               [(v.get("rate"), v.get("amount")) for v in truth["vat_breakdown"]],
               [(v.get("rate"), v.get("amount")) for v in data.get("vat_breakdown") or []])
    return outcomes, wrong


# ---------- Exécution ----------
def run_case(path: Path) -> dict:
    mime = MIMES[path.suffix.lower()]
    t0 = time.monotonic()
    out = {"file": path.name, "ok": True, "provider": settings.LLM_PROVIDER}
    tokens_in = tokens_out = 0
    try:
        doc = reader.read_document(path, mime)
        out["mode"] = doc.mode
        doc_type, cls = classifier.classify(doc)
        out["doc_type"], out["doc_type_by"] = doc_type, ("ai" if cls else "rules")
        if cls:
            tokens_in += cls.input_tokens
            tokens_out += cls.output_tokens
        defn = REGISTRY.get(doc_type)
        if defn:
            ext = extractor.extract(defn, doc)
            out.update(data=ext.data, issues=ext.issues, meta=ext.meta)
            tokens_in += ext.meta["input_tokens"]
            tokens_out += ext.meta["output_tokens"]
    except PipelineError as exc:
        out.update(ok=False, error=str(exc))
    except Exception as exc:  # une erreur inattendue ne doit pas arrêter tout l'essai
        out.update(ok=False, error=f"{type(exc).__name__}: {exc}")
    out.update(tokens_in=tokens_in, tokens_out=tokens_out, seconds=round(time.monotonic() - t0, 1))
    return out


def cmd_run(args) -> None:
    if args.provider:
        settings.LLM_PROVIDER = args.provider
    if args.fast:
        settings.LLM_MODEL_FAST = args.fast
    if args.strong is not None:
        settings.LLM_MODEL_STRONG = args.strong

    files = sorted(p for p in CASES.glob("*") if p.suffix.lower() in MIMES)
    if args.limit:
        files = files[: args.limit]
    if not files:
        print(f"Aucun document dans {CASES}")
        return

    out_dir = RUNS / args.name
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "_run.json").write_text(json.dumps({
        "name": args.name, "provider": settings.LLM_PROVIDER, "fast": settings.LLM_MODEL_FAST,
        "strong": settings.LLM_MODEL_STRONG, "date": datetime.now().isoformat(timespec="seconds"),
    }, indent=2), "utf-8")

    for i, path in enumerate(files, 1):
        target = out_dir / f"{path.name}.json"
        if target.exists() and not args.force:
            print(f"[{i}/{len(files)}] {path.name} : déjà fait (--force pour refaire)")
            continue
        print(f"[{i}/{len(files)}] {path.name} ...", end=" ", flush=True)
        res = run_case(path)
        target.write_text(json.dumps(res, ensure_ascii=False, indent=2), "utf-8")
        print("ok" if res["ok"] else f"ERREUR : {res['error']}", f"({res['seconds']} s)")


# ---------- Bonnes réponses ----------
def _results(name: str):
    return sorted(p for p in (RUNS / name).glob("*.json") if not p.name.startswith("_"))


def cmd_init_truth(args) -> None:
    TRUTH.mkdir(parents=True, exist_ok=True)
    created = 0
    for p in _results(args.name):
        target = TRUTH / p.name
        if target.exists():
            continue
        res = json.loads(p.read_text("utf-8"))
        data = res.get("data") or {}
        draft = {"_verified": False, "doc_type": res.get("doc_type")}
        for f in SCALARS:
            if f in data:
                draft[f] = data[f]
        if "lines" in data:
            draft["lines"] = [{"description": l.get("description"), "total_ht": l.get("total_ht")} for l in data["lines"]]
        if "vat_breakdown" in data:
            draft["vat_breakdown"] = [{k: v.get(k) for k in ("rate", "base", "amount")} for v in data["vat_breakdown"]]
        target.write_text(json.dumps(draft, ensure_ascii=False, indent=2), "utf-8")
        created += 1
    print(f"{created} fichiers créés dans {TRUTH}")
    print("Pour chacun : compare avec le VRAI document, corrige, puis mets \"_verified\": true.")


# ---------- Notation ----------
def _pct(a, b) -> str:
    return f"{100 * a / b:.0f} %" if b else "n/a"


def _tags(filename: str):
    return [t for t in re.split(r"[_\-. ]+", Path(filename).stem.lower()) if t and not t.isdigit()]


def cmd_score(args) -> dict:
    run_dir = RUNS / args.name
    meta = json.loads((run_dir / "_run.json").read_text("utf-8")) if (run_dir / "_run.json").exists() else {}
    per_field = defaultdict(lambda: [0, 0])
    tags = defaultdict(lambda: [0, 0])
    cls_ok = cls_total = scored = exact = flagged_n = silent = caught = false_alarms = escalated = 0
    tok_in = tok_out = secs = 0.0
    failures, unverified = [], []

    for p in _results(args.name):
        name = p.name[:-5]
        res = json.loads(p.read_text("utf-8"))
        tp = TRUTH / p.name
        truth = json.loads(tp.read_text("utf-8")) if tp.exists() else None
        if not truth or truth.get("_verified") is not True:
            unverified.append(name)
            continue
        if "doc_type" in truth:
            cls_total += 1
            cls_ok += truth["doc_type"] == res.get("doc_type")
        outcomes, wrong = check_case(truth, res)
        if not outcomes:
            continue  # pas de champs à évaluer (ex. CV pour l'instant)

        scored += 1
        for f, ok in outcomes.items():
            per_field[f][0] += ok
            per_field[f][1] += 1
        is_exact, flagged = not wrong, bool(res.get("issues"))
        exact += is_exact
        flagged_n += flagged
        if is_exact:
            false_alarms += flagged
        elif flagged:
            caught += 1
        else:
            silent += 1
        escalated += bool((res.get("meta") or {}).get("escalated"))
        tok_in += res.get("tokens_in", 0)
        tok_out += res.get("tokens_out", 0)
        secs += res.get("seconds", 0)
        for t in _tags(name):
            tags[t][0] += is_exact
            tags[t][1] += 1
        if wrong:
            failures.append((name, wrong, flagged, res.get("error")))

    field_ok_n = sum(v[0] for v in per_field.values())
    field_n = sum(v[1] for v in per_field.values())
    report = {
        "name": args.name, "provider": meta.get("provider"), "fast": meta.get("fast"), "strong": meta.get("strong"),
        "scored": scored, "unverified": len(unverified), "exact": exact,
        "classification": [cls_ok, cls_total], "fields": [field_ok_n, field_n],
        "flagged": flagged_n, "silent_errors": silent, "caught_errors": caught, "false_alarms": false_alarms,
        "escalated": escalated,
        "avg_tokens_in": round(tok_in / scored) if scored else 0, "avg_tokens_out": round(tok_out / scored) if scored else 0,
        "avg_seconds": round(secs / scored, 1) if scored else 0,
        "per_field": dict(per_field),
    }
    (run_dir / "_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")

    print(f"\n=== {args.name} : {meta.get('provider')} / {meta.get('fast')} (relance : {meta.get('strong') or 'aucune'}) ===")
    print(f"Documents évalués : {scored} (ignorés car non vérifiés : {len(unverified)})")
    print(f"Classification du type : {cls_ok}/{cls_total}")
    print(f"Documents entièrement corrects : {exact}/{scored} ({_pct(exact, scored)})")
    print(f"Champs corrects : {field_ok_n}/{field_n} ({_pct(field_ok_n, field_n)})")
    print(f"Documents signalés à relire : {flagged_n}/{scored}")
    print(f"ERREURS SILENCIEUSES (fausses et non signalées) : {silent}   <- le chiffre à faire tomber à 0")
    print(f"Erreurs signalées (bien rattrapées) : {caught} | fausses alertes : {false_alarms}")
    print(f"Moyenne par document : {report['avg_tokens_in']} jetons en entrée, {report['avg_tokens_out']} en sortie, "
          f"{report['avg_seconds']} s | relances par le second modèle : {escalated}")

    print("\nPar champ (du plus faible au plus fort) :")
    for f, (a, b) in sorted(per_field.items(), key=lambda kv: kv[1][0] / kv[1][1]):
        print(f"  {f:22} {a}/{b}  {_pct(a, b)}")

    groups = [(t, v) for t, v in tags.items() if v[1] >= 2]
    if groups:
        print("\nPar catégorie (étiquettes du nom de fichier, documents entièrement corrects) :")
        for t, (a, b) in sorted(groups, key=lambda kv: kv[1][0] / kv[1][1]):
            print(f"  {t:16} {a}/{b}  {_pct(a, b)}")

    if args.verbose and failures:
        print("\nDétail des erreurs :")
        for name, wrong, flagged, error in failures:
            print(f"  {name}  [{'signalé' if flagged else 'NON SIGNALÉ'}]" + (f"  erreur : {error}" if error else ""))
            for field, exp, got in wrong:
                print(f"     {field}: attendu {exp!r}, obtenu {got!r}")
    if unverified:
        print("\nNon vérifiés (ignorés) :", ", ".join(unverified))
    return report


def cmd_compare(args) -> None:
    rows = []
    for n in args.names:
        rp = RUNS / n / "_report.json"
        if not rp.exists():
            print(f"Pas de rapport pour « {n} » : lance d'abord « score --name {n} »")
            continue
        rows.append(json.loads(rp.read_text("utf-8")))
    if not rows:
        return
    print(f"\n{'essai':18}{'corrects':>10}{'champs':>9}{'silenc.':>9}{'à relire':>10}{'jetons e/s':>14}{'sec.':>7}")
    for r in rows:
        print(f"{r['name']:18}{_pct(r['exact'], r['scored']):>10}{_pct(*r['fields']):>9}{r['silent_errors']:>9}"
              f"{r['flagged']:>10}{str(r['avg_tokens_in']) + '/' + str(r['avg_tokens_out']):>14}{r['avg_seconds']:>7}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Évaluation du pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="traite les documents de eval/cases")
    r.add_argument("--name", required=True)
    r.add_argument("--provider")
    r.add_argument("--fast")
    r.add_argument("--strong")
    r.add_argument("--force", action="store_true")
    r.add_argument("--limit", type=int)
    t = sub.add_parser("init-truth", help="crée des réponses brouillon à corriger")
    t.add_argument("--name", required=True)
    s = sub.add_parser("score", help="compare aux réponses vérifiées")
    s.add_argument("--name", required=True)
    s.add_argument("-v", "--verbose", action="store_true")
    c = sub.add_parser("compare", help="compare plusieurs essais")
    c.add_argument("names", nargs="+")

    args = parser.parse_args()
    {"run": cmd_run, "init-truth": cmd_init_truth, "score": cmd_score, "compare": cmd_compare}[args.cmd](args)


if __name__ == "__main__":
    main()
from collections import Counter, defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models import User
from app.services.cross_checks import invoices_of, norm_id, supplier_key

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("")
def list_suppliers(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    groups = defaultdict(list)
    for doc in invoices_of(db, user.company_id):
        key = supplier_key(doc.extracted_data)
        if key:
            groups[key].append(doc)

    out = []
    for key, docs in groups.items():
        datas = [d.extracted_data for d in docs]
        totals, ibans = Counter(), Counter()
        for d in datas:
            if isinstance(d.get("total_ttc"), (int, float)):
                totals[d.get("currency") or "?"] += d["total_ttc"]
            if d.get("iban"):
                ibans[norm_id(d["iban"])] += 1
        dates = sorted(d["invoice_date"] for d in datas if d.get("invoice_date"))
        out.append({
            "key": key,
            "name": Counter(d.get("supplier_name") for d in datas if d.get("supplier_name")).most_common(1)[0][0] if any(d.get("supplier_name") for d in datas) else key,
            "siret": next((d["supplier_siret"] for d in datas if d.get("supplier_siret")), None),
            "vat_number": next((d["supplier_vat_number"] for d in datas if d.get("supplier_vat_number")), None),
            "invoice_count": len(docs),
            "totals": [{"currency": c, "total": round(t, 2)} for c, t in totals.items()],
            "last_date": dates[-1] if dates else None,
            "ibans": [{"iban": i, "count": n} for i, n in ibans.most_common()],
            "invoices": [
                {"document_id": d.id, "number": d.extracted_data.get("invoice_number"), "date": d.extracted_data.get("invoice_date"),
                 "total_ttc": d.extracted_data.get("total_ttc"), "currency": d.extracted_data.get("currency"), "filename": d.original_filename}
                for d in sorted(docs, key=lambda x: x.extracted_data.get("invoice_date") or "", reverse=True)
            ],
        })
    return sorted(out, key=lambda s: -s["invoice_count"])
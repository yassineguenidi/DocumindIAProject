from datetime import date

from app.services.pipeline.validators import parse_ym


def cv_derived(d: dict) -> dict:
    """Expérience totale en fusionnant les périodes qui se chevauchent."""
    now = date.today()
    now_idx = now.year * 12 + now.month - 1
    spans = []
    for e in d.get("experiences") or []:
        start = parse_ym(e.get("start_date"))
        if not start:
            continue
        end = parse_ym(e.get("end_date"), as_end=True)
        begin = start[0] * 12 + start[1] - 1
        if end:
            finish = end[0] * 12 + end[1] - 1
        elif e.get("is_current"):
            finish = now_idx
        else:
            continue
        finish = min(finish, now_idx)
        if finish >= begin:
            spans.append((begin, finish))

    total, cur_s, cur_e = 0, None, None
    for s, e in sorted(spans):
        if cur_e is None or s > cur_e:
            if cur_e is not None:
                total += cur_e - cur_s + 1
            cur_s, cur_e = s, e
        else:
            cur_e = max(cur_e, e)
    if cur_e is not None:
        total += cur_e - cur_s + 1
    return {"total_experience_months": total, "total_experience_years": round(total / 12, 1)}
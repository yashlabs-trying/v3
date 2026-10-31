def normalize(records):
    out = []
    for rec in records:
        if not any(str(k).strip().lower() == "id" for k in rec):
            continue
        for k in list(rec.keys()):
            v = rec.pop(k)
            rec[str(k).strip().lower()] = v.strip() if isinstance(v, str) else v
        out.append(rec)
    return out

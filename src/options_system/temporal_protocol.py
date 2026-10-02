from datetime import date

def add_label_end_dates(rows,horizons=(1,3,5,10)):
    out=[]
    for i,r in enumerate(rows):
        z=dict(r)
        for h in horizons:
            z[f"label_end_h{h}"]=rows[i+h]["date"] if i+h<len(rows) else None
        out.append(z)
    return out

def temporal_split(rows,train_end,validation_end,horizon=10):
    train=[]; validation=[]; oos=[]
    for r in rows:
        d=r["date"]; e=r.get(f"label_end_h{horizon}")
        if d<=train_end:
            if e is not None and e<=train_end: train.append(r)
        elif d<=validation_end:
            if e is not None and e<=validation_end: validation.append(r)
        else:
            if e is not None: oos.append(r)
    return {"train":train,"validation":validation,"oos":oos}

def assert_no_overlap(split,horizon=10):
    for name in ("train","validation"):
        rows=split[name]
        if not rows: continue
        boundary=max(r["date"] for r in rows)
        if any(r[f"label_end_h{horizon}"]>boundary for r in rows):
            raise AssertionError(f"Label leakage in {name}")
    return True

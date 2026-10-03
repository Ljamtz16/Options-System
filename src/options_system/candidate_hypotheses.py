def _f(x):
    try:return float(x)
    except (TypeError,ValueError):return None

def rule_applies(row,rule):
    v=_f(row.get(rule['feature']))
    if v is None:return False
    t=float(rule['value'])
    return v<=t if rule['op']=='<=' else v>t if rule['op']=='>' else False

def candidate_active(candidate,row):
    return all(rule_applies(row,r) for r in candidate['rules'])

def annotate_candidates(rows,candidates):
    out=[]
    for row in rows:
        x=dict(row)
        x['active_candidates']=';'.join(c['id'] for c in candidates if candidate_active(c,row))
        out.append(x)
    return out

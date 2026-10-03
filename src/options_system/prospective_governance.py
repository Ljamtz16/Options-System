import hashlib,json
from pathlib import Path

REVIEW_DAYS=(5,10,20,30)

def canonical_hash(obj):
    raw=json.dumps(obj,sort_keys=True,separators=(',',':')).encode()
    return hashlib.sha256(raw).hexdigest()

def session_manifest(meta,day,rows):
    contracts=sorted({r.get(k) for r in rows for k in ('call_contract','put_contract') if r.get(k)})
    times=sorted(r.get('captured_at_utc') for r in rows if r.get('captured_at_utc'))
    return {'schema':'prospective_session_manifest_v01','decision_date':day,
            'hypothesis_version':meta['version'],'frozen_at':meta['frozen_at'],
            'hypotheses_sha256':canonical_hash(meta['hypotheses']),
            'snapshot_rows':len(rows),'first_snapshot_utc':times[0] if times else None,
            'last_snapshot_utc':times[-1] if times else None,'contracts':contracts}

def daily_rows(rows,hypotheses,freeze):
    out=[]
    days=sorted({r.get('decision_date') for r in rows if r.get('decision_date') and r.get('decision_date')>freeze})
    for day in days:
        dr=[r for r in rows if r.get('decision_date')==day]
        for h in hypotheses:
            hid=h['id'];side=h['side'];hz=h['horizon_min']
            hit=[r for r in dr if hid in (r.get('active_hypotheses') or '').split(';')]
            vals=[float(r[f'{side}_ret_{hz}m']) for r in hit if r.get(f'{side}_ret_{hz}m') not in (None,'')]
            mfe=[float(r[f'{side}_mfe_{hz}m']) for r in hit if r.get(f'{side}_mfe_{hz}m') not in (None,'')]
            mae=[float(r[f'{side}_mae_{hz}m']) for r in hit if r.get(f'{side}_mae_{hz}m') not in (None,'')]
            touch=[r.get(f'{side}_{hz}m_tp10_sl10') for r in hit]
            out.append({'decision_date':day,'hypothesis':hid,'activated':bool(hit),
                        'n_signals':len(hit),'first_signal_utc':hit[0].get('captured_at_utc') if hit else None,
                        'mean_return':sum(vals)/len(vals) if vals else None,
                        'best_mfe':max(mfe) if mfe else None,'worst_mae':min(mae) if mae else None,
                        'tp_first':sum(x=='TP_FIRST' for x in touch),'sl_first':sum(x=='SL_FIRST' for x in touch),
                        'daily_result':('POSITIVE' if vals and sum(vals)/len(vals)>0 else
                                        'NON_POSITIVE' if vals else 'NO_OUTCOME')})
    return out

def scoreboard(daily,hypotheses):
    total_days=len({r['decision_date'] for r in daily});out={}
    next_review=next((x for x in REVIEW_DAYS if total_days<x),None)
    for h in hypotheses:
        rs=[r for r in daily if r['hypothesis']==h['id']];active=[r for r in rs if r['activated']]
        vals=[r['mean_return'] for r in active if r['mean_return'] is not None]
        decided=sum(r['tp_first']+r['sl_first'] for r in active);tp=sum(r['tp_first'] for r in active)
        out[h['id']]={'prospective_days':total_days,'activated_days':len(active),
                      'activations':sum(r['n_signals'] for r in active),
                      'mean_daily_return':sum(vals)/len(vals) if vals else None,
                      'positive_days':sum(v>0 for v in vals),'tp10_before_sl10_rate':tp/decided if decided else None,
                      'status':'INSUFFICIENT_SAMPLE' if total_days<5 else 'MONITOR',
                      'next_review_day':next_review}
    return out

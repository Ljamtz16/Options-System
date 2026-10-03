from collections import defaultdict
from datetime import datetime
from .candidate_hypotheses import candidate_active

def candidate_episodes(rows,candidate,max_gap_minutes=6):
    active=sorted([r for r in rows if candidate_active(candidate,r)],key=lambda r:r.get('captured_at_utc',''))
    grouped=[];cur=None;prev=None;prev_day=None
    for r in active:
        ts=datetime.fromisoformat(r['captured_at_utc']);day=r.get('decision_date')
        if cur is None or day!=prev_day or prev is None or (ts-prev).total_seconds()>max_gap_minutes*60:
            cur=[];grouped.append(cur)
        cur.append(r);prev=ts;prev_day=day
    return grouped

def evaluate_candidate_days(rows,candidate,exclude_through='2026-10-02',max_gap_minutes=6):
    side=candidate['side'];hz=candidate['horizon_min'];touch_key=f'{side}_{hz}m_tp10_sl10'
    by_day=defaultdict(list)
    for e in candidate_episodes(rows,candidate,max_gap_minutes):
        if not e:continue
        first=e[0];day=first.get('decision_date')
        if not day or day<=exclude_through:continue
        touch=first.get(touch_key)
        by_day[day].append({'start':first.get('captured_at_utc'),'activations':len(e),
                            'contract':first.get(f'{side}_contract'),'touch':touch,
                            'tp_before_sl':1 if touch=='TP_FIRST' else 0 if touch=='SL_FIRST' else None,
                            'return':first.get(f'{side}_ret_{hz}m'),'mfe':first.get(f'{side}_mfe_{hz}m'),'mae':first.get(f'{side}_mae_{hz}m')})
    days=[]
    for day in sorted(by_day):
        eps=by_day[day];dec=[e for e in eps if e['tp_before_sl'] is not None]
        days.append({'decision_date':day,'episodes':len(eps),'decided':len(dec),
                     'tp_first':sum(e['tp_before_sl'] for e in dec),
                     'tp_before_sl_rate':sum(e['tp_before_sl'] for e in dec)/len(dec) if dec else None,
                     'episode_rows':eps})
    return days

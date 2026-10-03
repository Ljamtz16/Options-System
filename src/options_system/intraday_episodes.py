from datetime import datetime
from options_system.option_costs import one_contract_trade

def group_episodes(rows,active_key='h03',max_gap_minutes=6):
    active=[r for r in rows if r.get(active_key)]
    active=sorted(active,key=lambda r:r.get('captured_at_utc',''))
    out=[];cur=None;prev=None
    for r in active:
        ts=datetime.fromisoformat(r['captured_at_utc'])
        if cur is None or prev is None or (ts-prev).total_seconds()>max_gap_minutes*60:
            cur={'start':r['captured_at_utc'],'end':r['captured_at_utc'],'rows':[r]}
            out.append(cur)
        else:
            cur['end']=r['captured_at_utc'];cur['rows'].append(r)
        prev=ts
    return out

def summarize_episodes(rows,active_key='h03',side='call',horizon=60,max_gap_minutes=6):
    out=[]
    for i,e in enumerate(group_episodes(rows,active_key,max_gap_minutes),1):
        x=e['rows'][0];touch=x.get(f'{side}_{horizon}m_tp10_sl10')
        out.append({'episode_id':f'E{i}','start':e['start'],'end':e['end'],
                    'activation_count':len(e['rows']),
                    'duration_minutes':max(0,(datetime.fromisoformat(e['end'])-datetime.fromisoformat(e['start'])).total_seconds()/60),
                    'contract':x.get(f'{side}_contract'),'entry_ask':x.get(f'{side}_entry_ask'),
                    'return':x.get(f'{side}_ret_{horizon}m'),'mfe':x.get(f'{side}_mfe_{horizon}m'),
                    'mae':x.get(f'{side}_mae_{horizon}m'),'tp_sl':touch,
                    'tp_before_sl':None if not touch or touch=='AMBIGUOUS' or touch=='NEITHER' else int(touch=='TP_FIRST'),
                    'exit_return':x.get(f'{side}_{horizon}m_tp10_sl10_exit_return'),
                    'trade_1_contract':one_contract_trade(x.get(f'{side}_entry_ask'),x.get(f'{side}_{horizon}m_tp10_sl10_exit_return'))})
    return out

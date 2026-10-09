"""Prepared views: one session per request, with no raw-data work in the browser."""
import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from .session_cache import NY, atomic_text, today


def row_day(row):
    for key in ('decision_date','market_date','session_date'):
        if row.get(key):return str(row[key])[:10]
    for key in ('local_entry_time','entry_time','signal_time','created_at','timestamp','start'):
        stamp=row.get(key)
        if stamp:
            try:return datetime.fromisoformat(str(stamp).replace('Z','+00:00')).astimezone(NY).date().isoformat()
            except ValueError:pass
    signal=row.get('signal_id','')
    for part in signal.split(':'):
        if len(part)==10 and part[4:5]=='-' and part[7:8]=='-':return part
    return None


def scope_meta(meta, day):
    value=copy.deepcopy(meta)
    paper=value.get('paper_trading',{})
    ledger=[r for r in paper.get('live_ledger',[]) if row_day(r)==day]
    paper['live_ledger']=ledger
    paper['session_realized_net_pnl']=sum(float(r.get('net_pnl') or 0) for r in ledger if r.get('status')=='CLOSED')
    paper['session_date']=day
    oa=value.get('options_alpaca_paper',{})
    oa['trades']={k:r for k,r in oa.get('trades',{}).items() if row_day(r)==day}
    oa['last_actions']=[r for r in oa.get('last_actions',[]) if row_day(r)==day]
    ja=value.get('jev_alpaca_paper',{})
    ja['orders']=[r for r in ja.get('orders',[]) if row_day(r)==day]
    validation=value.get('prospective_validation',{})
    validation['prospective_episodes']=[r for r in validation.get('prospective_episodes',[]) if row_day(r)==day]
    account=validation.get('virtual_account',{})
    account['ledger']=[r for r in account.get('ledger',[]) if row_day(r)==day]
    gate=value.get('execution_gate',{})
    gate['episodes']=[r for r in gate.get('episodes',[]) if row_day(r)==day]
    from collections import Counter
    gate['counts']=dict(Counter((r.get('execution_gate') or {}).get('status','UNKNOWN') for r in gate['episodes']))
    for key in ('seen_signal_ids','previous_snapshot_cursor'):
        paper.pop(key,None)
    for key in ANALYSIS_KEYS:
        value.pop(key,None)
    value['view_scope']={'day':day,'accounts':'CURRENT_BALANCES','analysis':'CACHED_POSTCLOSE'}
    return value


def publish_sessions(directory, rows, meta=None):
    directory=Path(directory)
    groups={}
    for row in rows:groups.setdefault(row['decision_date'],[]).append(row)
    groups.setdefault(today(),[])
    index=[]
    for day,items in sorted(groups.items()):
        encoded=json.dumps(items,separators=(',',':'))
        target=directory/(day+'.json')
        if not target.exists() or target.read_text()!=encoded:atomic_text(target,encoded)
        index.append(dict(day=day,rows=len(items),symbols=sorted({r.get('symbol','SPY') for r in items}),
                          latest_capture=max((r.get('captured_at_utc') or '' for r in items),default=None)))
        if meta is not None:
            atomic_text(directory/(day+'.meta.json'),json.dumps(scope_meta(meta,day),separators=(',',':')))
    manifest=dict(version=1,today=today(),generated_at_utc=datetime.now(timezone.utc).isoformat(),sessions=index)
    atomic_text(directory/'index.json',json.dumps(manifest,separators=(',',':')))
    return groups.get(today(),[])

ANALYSIS_KEYS=('entry_controls_analysis','jev_calibration_analysis','paper_risk_comparison','discovery',
               'sizing_simulation','stress_testing','tracker_summary','prospective')


def publish_meta_views(directory,meta,refresh_closed=False):
    directory=Path(directory)
    manifest=json.loads((directory/'index.json').read_text())
    encoded=json.dumps({k:meta.get(k,{}) for k in ANALYSIS_KEYS},separators=(',',':'))
    target=directory/'analysis.json'
    if not target.exists() or target.read_text()!=encoded:atomic_text(target,encoded)
    for record in manifest['sessions']:
        day=record['day'];target=directory/(day+'.meta.json')
        if day==today() or refresh_closed or not target.exists():
            atomic_text(target,json.dumps(scope_meta(meta,day),separators=(',',':')))


def publish_web(source,web,assets):
    import os,shutil,tempfile
    source,web=Path(source),Path(web)
    paths=[*[p for p in sorted((source/'sessions').glob('*.json')) if p.name!='views-cache.json'],*[source/name for name in assets]]
    # Publish the manifest and HTML after their dependencies.
    paths.sort(key=lambda p:p.name in ('index.json','intraday_research_dashboard.html'))
    for path in paths:
        relative=path.relative_to(source);target=web/relative
        if not path.exists():continue
        stat=path.stat()
        if target.exists() and target.stat().st_size==stat.st_size and target.stat().st_mtime_ns==stat.st_mtime_ns:
            # mkstemp defaults to 0600, but Nginx serves these copies as www-data.
            # Repair the web copy even when content did not change.
            if target.stat().st_mode & 0o777 != 0o644:target.chmod(0o644)
            continue
        target.parent.mkdir(parents=True,exist_ok=True)
        fd,name=tempfile.mkstemp(dir=target.parent,prefix=target.name+'.',suffix='.tmp');os.close(fd)
        try:
            shutil.copy2(path,name)
            # Only the published copy is made readable; source artifacts keep their mode.
            os.chmod(name,0o644);os.replace(name,target)
        finally:
            if os.path.exists(name):os.unlink(name)

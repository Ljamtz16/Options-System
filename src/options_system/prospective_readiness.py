import json
from datetime import datetime, timezone
from pathlib import Path

def _load(path, default=None):
    try: return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError): return {} if default is None else default

def build_health(root, now=None):
    root=Path(root); now=now or datetime.now(timezone.utc); a=root/"artifacts"/"intraday"
    freeze=_load(a/"FROZEN_HYPOTHESES_V02.json",{}); gate=_load(a/"PROSPECTIVE_RISK_GATE_V01.json",{})
    execution=_load(a/"PROSPECTIVE_EXECUTION_GATE_V01.json",{}); report=_load(a/"HYPOTHESIS_DAILY_REPORT_V02.json",{})
    raw=root/"data"/"raw"/"prospective"; snaps=sorted(raw.glob("spy_options_*.json")) if raw.exists() else []
    latest=datetime.fromtimestamp(max(x.stat().st_mtime for x in snaps),tz=timezone.utc) if snaps else None
    h03=next((h for h in freeze.get("hypotheses",[]) if h.get("id")=="H03_CALL_RELATIVE_WEAKNESS_REVERSAL_V01"),None)
    start=(h03 or {}).get("prospective_start_after"); episodes=report.get("prospective_episodes",[])
    dates=sorted({e.get("decision_date") for e in episodes if e.get("decision_date")})
    counts=execution.get("counts") or {"PASS":0,"BLOCK":0,"REVIEW_MISSING_MARKET_QUALITY":0}
    checks=[
      {"id":"h03_frozen","label":"H03 frozen","status":"PASS" if h03 and start else "FAIL","detail":f"prospective_start_after={start}" if start else "freeze metadata missing"},
      {"id":"raw_snapshots","label":"Raw SPY snapshots","status":"PASS" if snaps else "FAIL","detail":f"{len(snaps)} snapshots; latest={latest.isoformat() if latest else '--'}"},
      {"id":"prospective_evidence","label":"Prospective evidence","status":"PASS" if dates else "WAITING","detail":f"{len(episodes)} episodes across {len(dates)} dates" if dates else "No post-freeze episode settled yet"},
      {"id":"risk_gate","label":"Risk gate","status":"PASS" if gate.get("status") in ("ACTIVE","BLOCKED") else "FAIL","detail":f"{gate.get('status','UNKNOWN')} / max={gate.get('allowed_max_fraction',0):.0%}"},
      {"id":"execution_gate","label":"Execution gate","status":"PASS" if execution.get("counts") is not None else "FAIL","detail":f"PASS={counts['PASS']} BLOCK={counts['BLOCK']} REVIEW={counts['REVIEW_MISSING_MARKET_QUALITY']}"},
      {"id":"dashboard_meta","label":"Dashboard metadata","status":"PASS" if (a/"research_dashboard_meta.json").exists() else "FAIL","detail":"research_dashboard_meta.json present" if (a/"research_dashboard_meta.json").exists() else "missing"}]
    failures=sum(x["status"]=="FAIL" for x in checks); waiting=sum(x["status"]=="WAITING" for x in checks)
    overall="NOT_READY" if failures else ("WAITING_MARKET_DATA" if waiting else "READY")
    return {"version":"v0.1","generated_at_utc":now.isoformat(),"overall_status":overall,"failures":failures,"waiting":waiting,"snapshot_count":len(snaps),"latest_snapshot_utc":latest.isoformat() if latest else None,"prospective_episode_count":len(episodes),"checks":checks,"notes":["System health is operational readiness, not scientific evidence.","Collector service/timer liveness must be verified on the VPS with systemd; this artifact verifies persisted outputs, not process state."]}

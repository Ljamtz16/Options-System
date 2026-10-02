import json
from src.options_system import historical_orchestrator as ho

def test_session_resume(monkeypatch,tmp_path):
    calls=[]
    monkeypatch.setattr(ho,"fetch_pages",lambda kind,symbol,start,end,out,resume=True:calls.append((kind,symbol)))
    u=[{"option_symbol":"A"},{"option_symbol":"B"}]
    a=ho.run_session("2026-01-01",u,"s","e",tmp_path)
    assert a["completed"]==2 and len(calls)==4
    b=ho.run_session("2026-01-01",u,"s","e",tmp_path)
    assert b["completed"]==2 and len(calls)==4

from src.options_system import bars_backfill as bb

def test_bars_only_resume(monkeypatch,tmp_path):
    calls=[]
    monkeypatch.setattr(bb,"fetch_pages",lambda *a,**k:calls.append(a[1]))
    u=[{"option_symbol":"A"},{"option_symbol":"B"}]
    assert bb.run_session_bars("d",u,"s","e",tmp_path,workers=2)["completed"]==2
    assert bb.run_session_bars("d",u,"s","e",tmp_path,workers=2)["completed"]==2
    assert sorted(calls)==["A","B"]

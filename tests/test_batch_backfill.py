from src.options_system import batch_backfill as bb
def test_batch_resume_and_limit(monkeypatch,tmp_path):
    calls=[]; sleeps=[]
    monkeypatch.setattr(bb,"fetch_json",lambda k,p:(calls.append(dict(p)) or ({"bars":{}}, "u")))
    monkeypatch.setattr(bb,"save_snapshot",lambda *a,**k:None)
    xs=["A","B","C"]
    assert bb.fetch_bars_batch(xs,"s","e",tmp_path,batch_size=2,sleep_fn=sleeps.append,log_fn=lambda x:None)["completed"]==2
    bb.fetch_bars_batch(xs,"s","e",tmp_path,batch_size=2,sleep_fn=sleeps.append,log_fn=lambda x:None)
    assert [x["symbols"] for x in calls]==["A,B","C"]
    assert all(x["limit"]==10000 for x in calls)
    assert sleeps==[1.0,1.0]

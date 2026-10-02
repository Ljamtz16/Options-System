from src.options_system import historical_backfill as hb

def test_pagination_and_completed_resume(monkeypatch,tmp_path):
    calls=[]
    def fake(kind,params):
        calls.append(dict(params))
        if len(calls)==1: return ({kind:{"X":[{"t":"a"}]},"next_page_token":"NEXT"},"u1")
        return ({kind:{"X":[{"t":"b"}]},"next_page_token":None},"u2")
    def fake_save(payload,url,out):
        out.write_text("{}"); return {"sha256":"abc"}
    monkeypatch.setattr(hb,"fetch_json",fake)
    monkeypatch.setattr(hb,"save_snapshot",fake_save)
    m=hb.fetch_pages("bars","X","s","e",tmp_path)
    assert m["pages"]==2 and m["records"]==2
    assert calls[1]["page_token"]=="NEXT"
    m2=hb.fetch_pages("bars","X","s","e",tmp_path)
    assert m2==m and len(calls)==2

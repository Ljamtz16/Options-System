from src.options_system import prospective_collector as pc

def test_chain_filter_is_bounded(monkeypatch):
    captured={}
    monkeypatch.setattr(pc,"_get",lambda base,path,params=None:(captured.update(params or {}) or {"snapshots":{}}))
    pc.option_chain(100,dte_min=1,dte_max=10,width_pct=.04)
    assert captured["strike_price_gte"] == 96.0
    assert captured["strike_price_lte"] == 104.0
    assert captured["limit"] == 1000

def test_collector_default_feed_is_indicative(monkeypatch):
    captured={}
    monkeypatch.setattr(pc,"_get",lambda base,path,params=None:(captured.update(params or {}) or {}))
    pc.option_chain(100)
    assert captured["feed"] == "indicative"

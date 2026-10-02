from src.options_system import historical_pipeline as hp

def test_day_wires_reference_to_universe(monkeypatch,tmp_path):
    monkeypatch.setattr(hp,"spy_reference_at",lambda *a:{"price":100.0,"timestamp":"t","field":"open"})
    monkeypatch.setattr(hp,"fetch_contracts_all_statuses",lambda p:[
        {"symbol":"X","type":"call","strike_price":"100","expiration_date":"2026-01-02"}])
    monkeypatch.setattr(hp,"run_session",lambda *a,**k:{"completed":1})
    r=hp.run_day("2026-01-01","s","e",tmp_path)
    assert r["universe_count"]==1 and r["spy_reference"]["price"]==100.0

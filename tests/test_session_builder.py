import json
from src.options_system import session_builder as sb

def test_session_manifest_is_frozen(monkeypatch,tmp_path):
    monkeypatch.setattr(sb,"causal_spot_reference",lambda *a,**k:{"price":100.0,"observed_at_utc":"t","basis":"b","feed":"iex","source_url":"u"})
    monkeypatch.setattr(sb,"fetch_contracts_all_statuses",lambda p:[
      {"symbol":"X","type":"call","strike_price":"100","expiration_date":"2026-01-02"}])
    a=sb.prepare_session("2026-01-01","s","e",tmp_path)
    b=sb.prepare_session("2026-01-01","s","e",tmp_path)
    assert a==b and a["contract_count"]==1

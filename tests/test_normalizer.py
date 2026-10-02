import json
from src.options_system.normalizer import normalize_session
def test_normalize(tmp_path):
 raw=tmp_path/"raw"; raw.mkdir()
 (raw/"batch_0000_page_0001.json").write_text(json.dumps({"payload":{"bars":{"X":[{"t":"2024-01-01T14:30:00Z","o":1,"h":2,"l":.5,"c":1.5,"v":10,"n":2,"vw":1.2}]}}}))
 m=tmp_path/"u.json"; m.write_text(json.dumps({"universe":[{"option_symbol":"X","option_type":"call","strike":100.0,"expiration_date":"2024-01-05","dte":4,"spot_reference":100.0}]}))
 r=normalize_session(raw,m)
 assert len(r)==1 and r[0]["close"]==1.5 and r[0]["option_type"]=="call"

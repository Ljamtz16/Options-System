import json
from src.options_system.quality_gate import quality_session
def test_zero_bars_fails(tmp_path):
 r=tmp_path/"r";r.mkdir();(r/"batch_0000_page_0001.json").write_text(json.dumps({"payload":{"bars":{}}}))
 m=tmp_path/"u";m.write_text(json.dumps({"universe":[{"option_symbol":"X"}]}))
 q=quality_session(r,m); assert q["status"]=="QUALITY_FAIL" and "ZERO_BARS_FOR_NONEMPTY_UNIVERSE" in q["reasons"]
def test_normal_session_passes(tmp_path):
 r=tmp_path/"r";r.mkdir();(r/"batch_0000_page_0001.json").write_text(json.dumps({"payload":{"bars":{"X":[{"t":"T"}]}}}))
 m=tmp_path/"u";m.write_text(json.dumps({"universe":[{"option_symbol":"X"}]}))
 assert quality_session(r,m)["status"]=="PASS"

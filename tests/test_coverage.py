import json
from src.options_system.coverage import session_coverage

def test_zero_activity_is_preserved(tmp_path):
    root=tmp_path/"d"; (root/"A"/"bars").mkdir(parents=True); (root/"A"/"trades").mkdir()
    (root/"session_checkpoint.json").write_text(json.dumps({"completed":["A"]}))
    (root/"A"/"bars"/"bars_manifest.json").write_text(json.dumps({"records":0}))
    (root/"A"/"trades"/"trades_manifest.json").write_text(json.dumps({"records":0}))
    row=session_coverage(root)[0]
    assert row["bars"]==0 and row["has_bars"] is False

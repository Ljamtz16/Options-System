import json
from src.options_system.snapshot_store import write_immutable_snapshot, append_index

def test_snapshot_is_content_hashed_and_indexed(tmp_path):
    payload={"underlying":{"symbol":"SPY","bid":100,"ask":101},"chain":[]}
    path,digest=write_immutable_snapshot(payload,tmp_path/"snapshots")
    saved=json.loads(path.read_text())
    assert saved["sha256"] == digest
    assert saved["payload"] == payload
    idx=tmp_path/"index.jsonl"
    append_index(path,digest,idx)
    row=json.loads(idx.read_text().strip())
    assert row["sha256"] == digest
    assert row["path"] == str(path)

def test_two_captures_never_overwrite(tmp_path):
    payload={"x":1}
    p1,_=write_immutable_snapshot(payload,tmp_path)
    p2,_=write_immutable_snapshot(payload,tmp_path)
    assert p1 != p2
    assert p1.exists() and p2.exists()

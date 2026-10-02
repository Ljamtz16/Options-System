import json
from src.options_system import alpaca_history as ah

def test_credentials_false_when_missing(monkeypatch):
    monkeypatch.delenv("APCA_API_KEY_ID", raising=False)
    monkeypatch.delenv("APCA_API_SECRET_KEY", raising=False)
    assert ah.credentials_present() is False

def test_missing_credentials_fail_closed(monkeypatch):
    monkeypatch.delenv("APCA_API_KEY_ID", raising=False)
    monkeypatch.delenv("APCA_API_SECRET_KEY", raising=False)
    try:
        ah._headers()
        assert False, "Expected RuntimeError"
    except RuntimeError:
        pass

def test_snapshot_hash_is_deterministic(tmp_path):
    payload = {"bars": {"SPYTEST": [{"t": "2026-09-29T14:30:00Z", "c": 1.23}]}}
    meta = ah.save_snapshot(payload, "https://example.invalid/test", tmp_path / "snap.json")
    saved = json.loads((tmp_path / "snap.json").read_text())
    assert saved["metadata"]["sha256"] == meta["sha256"]
    assert saved["payload"] == payload

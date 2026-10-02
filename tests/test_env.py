from src.options_system.env import load_local_env

def test_load_local_env(tmp_path, monkeypatch):
    monkeypatch.delenv("APCA_API_KEY_ID", raising=False)
    monkeypatch.delenv("APCA_API_SECRET_KEY", raising=False)
    p = tmp_path / ".env"
    p.write_text("APCA_API_KEY_ID=test_key\nAPCA_API_SECRET_KEY=test_secret\n")
    assert load_local_env(p) is True
    import os
    assert os.environ["APCA_API_KEY_ID"] == "test_key"
    assert os.environ["APCA_API_SECRET_KEY"] == "test_secret"

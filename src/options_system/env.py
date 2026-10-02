from pathlib import Path

def load_local_env(path=None):
    env_path = Path(path) if path else Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return False
    import os
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in {"APCA_API_KEY_ID", "APCA_API_SECRET_KEY"}:
            os.environ.setdefault(key, value.strip())
    return True

import hashlib, json, uuid
from datetime import datetime, timezone
from pathlib import Path

def canonical_json(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def write_immutable_snapshot(payload, directory, prefix="spy_options"):
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%S.%fZ")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    raw = canonical_json(payload)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    capture_id = uuid.uuid4().hex[:12]
    path = directory / f"{prefix}_{stamp}_{capture_id}_{digest[:12]}.json"
    with path.open("x", encoding="utf-8") as f:
        envelope = {"captured_at_utc": now.isoformat(), "capture_id": capture_id,
                    "sha256": digest, "payload": payload}
        json.dump(envelope, f, indent=2, ensure_ascii=False)
    return path, digest

def append_index(path, digest, index_path):
    index_path = Path(index_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    row = {"path": str(path), "sha256": digest}
    with index_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")

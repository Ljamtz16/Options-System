import json
from pathlib import Path
from options_system.snapshot_store import write_immutable_snapshot, append_index

source=Path("data/raw/current_capture_input.json")
payload=json.loads(source.read_text(encoding="utf-8"))
path,digest=write_immutable_snapshot(payload,"data/raw/prospective","spy_options")
append_index(path,digest,"data/raw/prospective/index.jsonl")
print(f"snapshot={path}")
print(f"sha256={digest}")
print(f"contracts={len(payload['option_chain'])}")

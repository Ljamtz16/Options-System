import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_strategy_health_gate_is_shadow_only_and_future_partitioned():
    cfg=json.loads((ROOT/"config/strategy_health_gate_v01.json").read_text())
    assert cfg["mode"] == "SHADOW_ONLY"
    assert cfg["auto_apply"] is False
    assert cfg["broker_orders_enabled"] is False
    assert cfg["prospective_start_after"] == "2026-10-15"
    assert len(cfg["candidates"]) == 4
    assert all(c["block_if_any"] for c in cfg["candidates"])

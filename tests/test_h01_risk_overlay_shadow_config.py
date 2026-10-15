import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_h01_risk_overlay_shadow_is_non_operational_and_future_partitioned():
    cfg=json.loads((ROOT/"config/h01_risk_overlay_shadow_v01.json").read_text())
    assert cfg["mode"] == "SHADOW_ONLY"
    assert cfg["auto_apply"] is False
    assert cfg["broker_orders_enabled"] is False
    assert cfg["prospective_start_after"] == "2026-10-15"
    assert {c["id"] for c in cfg["candidates"]} == {"RO01_COOLDOWN15","RO02_SHG02","RO03_SHG02_COOLDOWN15"}

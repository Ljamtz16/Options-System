import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CFG = ROOT / "config/put_confirmation_shadow_v02.json"
SCRIPT = ROOT / "scripts/track_put_confirmation_shadow_v02.py"
OUT = ROOT / "artifacts/intraday/PUT_CONFIRM_SHADOW_V02_PROSPECTIVE.json"


def test_frozen_configuration():
    cfg = json.loads(CFG.read_text(encoding="utf-8"))

    assert cfg["version"] == "PUT_CONFIRM_SHADOW_V02"
    assert cfg["mode"] == "SHADOW_ONLY_NO_ORDERS"
    assert cfg["prospective_start_after"] == "2026-10-13"

    sm = cfg["state_machine"]

    assert sm["confirmation_min_minutes"] == 6
    assert sm["confirmation_max_minutes"] == 15
    assert sm["confirmation_requires_h06"] is True
    assert sm["post_signal_lock_minutes"] == 15
    assert sm["max_signals_per_arm"] == 1

    assert sm["confirmation_requires"] == [
        "spy_from_open < arm.spy_from_open",
        "qqq_from_open < arm.qqq_from_open",
        "iwm_from_open < arm.iwm_from_open",
    ]

    ev = cfg["execution_evaluation"]

    assert ev["side"] == "PUT"
    assert ev["horizon_minutes"] == 15
    assert ev["take_profit_pct"] == 0.10
    assert ev["stop_loss_pct"] == 0.10


def test_tracker_preserves_discovery_and_allows_prospective_growth():
    subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    result = json.loads(
        OUT.read_text(encoding="utf-8")
    )

    assert result["version"] == "PUT_CONFIRM_SHADOW_V02"
    assert result["mode"] == "SHADOW_ONLY_NO_ORDERS"
    assert result["prospective_start_after"] == "2026-10-13"

    assert result["h06_activations_total"] >= 15
    assert result["discovery_replay"]["signals"] == 1
    assert all(x["decision_date"] <= "2026-10-13" for x in result["discovery_replay"]["rows"])
    assert all(x["decision_date"] > "2026-10-13" for x in result["prospective"]["rows"])


def test_discovery_signal_is_all3_confirmation():
    result = json.loads(
        OUT.read_text(encoding="utf-8")
    )

    rows = result["discovery_replay"]["rows"]

    assert len(rows) == 1

    signal = rows[0]
    arm = signal["arm"]
    entry = signal["entry"]

    assert entry["spy_from_open"] < arm["spy_from_open"]
    assert entry["qqq_from_open"] < arm["qqq_from_open"]
    assert entry["iwm_from_open"] < arm["iwm_from_open"]

    gap = signal["confirmation_gap_minutes"]

    assert 6 <= gap <= 15

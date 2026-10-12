import sys
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from options_system.guarded_shadow import build_guarded_shadow

H = "CALL_FLOW_REVERSAL_V01"

def trade(i, entry, exit_, pnl, reason="SL10"):
    return {"signal_id":f"P{i}","hypothesis":H,"status":"CLOSED",
            "entry_time":entry,"signal_time":entry,"exit_time":exit_,
            "net_pnl":pnl,"exit_reason":reason}

def tracker():
    rows=[]; n=0
    for h in range(14,20):
        for m in range(0,60,5):
            rows.append({"captured_at_utc":f"2026-10-12T{h:02d}:{m:02d}:00+00:00","spy_price":100+n*.01})
            n+=1
    return rows

def test_halt_skip_and_regime_rearm():
    ledger=[
        trade(1,"2026-10-12T14:00:00+00:00","2026-10-12T14:10:00+00:00",-10),
        trade(2,"2026-10-12T14:15:00+00:00","2026-10-12T14:25:00+00:00",-10),
        trade(3,"2026-10-12T14:30:00+00:00","2026-10-12T14:40:00+00:00",-10),
        trade(4,"2026-10-12T14:45:00+00:00","2026-10-12T14:55:00+00:00",-10),
        trade(5,"2026-10-12T15:05:00+00:00","2026-10-12T15:10:00+00:00",-10),
        trade(6,"2026-10-12T15:30:00+00:00","2026-10-12T15:40:00+00:00",20,"TP10")]
    r=build_guarded_shadow({"live_ledger":ledger,"open_positions":[]},tracker(),generated_at=datetime(2026,10,12,tzinfo=timezone.utc))
    d={x["signal_id"]:x for x in r["decisions"]}
    assert d["P5"]["shadow_action"]=="WOULD_SKIP"
    assert d["P6"]["shadow_action"]=="WOULD_ENTER"
    assert d["P6"]["shadow_reason"]=="REARMED_REGIME"
    assert r["by_day"]["2026-10-12"]["halts"]==1
    assert r["by_day"]["2026-10-12"]["rearms"]==1

def test_skipped_trade_does_not_reset_shadow_streak():
    ledger=[trade(i,f"2026-10-12T14:{(i-1)*10:02d}:00+00:00",f"2026-10-12T14:{(i-1)*10+5:02d}:00+00:00",-10) for i in range(1,5)]
    ledger += [trade(5,"2026-10-12T14:45:00+00:00","2026-10-12T14:50:00+00:00",20,"TP10")]
    r=build_guarded_shadow({"live_ledger":ledger,"open_positions":[]},tracker(),{"minimum_halt_minutes":120})
    d={x["signal_id"]:x for x in r["decisions"]}
    assert d["P5"]["shadow_action"]=="WOULD_SKIP"
    assert r["by_day"]["2026-10-12"]["tp_sacrificed"]==1

def test_non_target_hypothesis_is_ignored():
    t=trade(1,"2026-10-12T14:00:00+00:00","2026-10-12T14:10:00+00:00",-10)
    t["hypothesis"]="PUT_SKEW_SHORT_V01"
    r=build_guarded_shadow({"live_ledger":[t],"open_positions":[]},tracker())
    assert r["decisions"]==[]

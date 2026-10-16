from options_system.meta_decision_live import (
    context_from_envelope,
    context_ready_for_day,
    episode_metrics,
    h01_decision,
    h09_decision,
    health_flags_from_closed,
    multi_decision,
)


def test_health_flags_are_causal_and_use_vix():
    rows=[{"exit_time":f"2026-10-16T14:0{i}:00+00:00","net_pnl":-10} for i in range(5)]
    flags=health_flags_from_closed(rows,0.06)
    assert "loss_streak_4" in flags
    assert "rolling5_winrate_below_20pct" in flags
    assert "vix_up_5pct" in flags


def test_h01_repeat_waits_without_block():
    decision, block, wait=h01_decision(True,[],"RISK_ON",True,True)
    assert decision=="WAIT"
    assert not block
    assert "CORRELATED_REPEAT_WITHIN_15M" in wait


def test_h01_health_block_has_priority():
    decision, block, wait=h01_decision(True,["loss_streak_4"],"RISK_ON",True,True)
    assert decision=="BLOCK"
    assert "HEALTH:loss_streak_4" in block
    assert wait


def test_h09a_waits_and_h09b_accepts_in_riskoff():
    d1,_,w1,_=h09_decision(False,"SPYPUT",2.0,1.95,"RISK_OFF",5.0,.12)
    d2,b2,_,_=h09_decision(True,"SPYPUT",2.0,1.95,"RISK_OFF",5.0,.12)
    assert d1=="WAIT" and w1
    assert d2=="ACCEPT" and not b2


def test_multi_two_support_waits_when_regime_aligned():
    d,b,w,_=multi_decision("CALL","QQQCALL",2.0,1.95,"RISK_ON",2,5.0,.12,2)
    assert d=="WAIT" and not b
    assert "REDUNDANT_SUPPORT_NOT_CONFIRMATION" in w


def test_episode_repeat_after_second_activation():
    hist=[]
    a=episode_metrics(hist,"H01","SPY","CALL","2026-10-16T14:00:00+00:00")
    hist.append({"source":"H01","symbol":"SPY","side":"CALL","time":"2026-10-16T14:00:00+00:00",**a})
    b=episode_metrics(hist,"H01","SPY","CALL","2026-10-16T14:05:00+00:00")
    assert not a["is_episode_repeat"]
    assert b["is_episode_repeat"]
    assert b["persistence_observations"]==2


def test_context_extracts_research_features():
    env={"captured_at_utc":"2026-10-16T14:00:00+00:00","payload":{"research_state":{"features":{
        "spy_from_open":.01,"qqq_from_open":.02,"iwm_from_open":.005,"vix_change_pct":-.03
    }}}}
    ctx=context_from_envelope(env)
    assert ctx["market_regime"]=="RISK_ON"
    assert ctx["vix_change_pct"]==-.03


def test_context_must_match_market_day():
    ctx={"captured_at_utc":"2026-10-15T19:59:00+00:00"}
    assert context_ready_for_day(ctx,"2026-10-15")
    assert not context_ready_for_day(ctx,"2026-10-16")

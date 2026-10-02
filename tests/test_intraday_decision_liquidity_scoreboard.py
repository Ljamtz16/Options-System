import csv,json
from pathlib import Path
from options_system.intraday_liquidity import evaluate_liquidity
from options_system.intraday_decision_engine import intraday_research_decision
from options_system.intraday_scoreboard import build_scoreboard

def test_liquidity_gate_pass_and_spread_block():
    good={"bid":1.0,"ask":1.1,"delta":.5,"bid_size":10,"ask_size":10}
    bad={"bid":.2,"ask":.5,"delta":.5}
    assert evaluate_liquidity(good)["pass"]
    assert evaluate_liquidity(bad)["reason"]=="SPREAD"

def test_intraday_decision_requires_direction():
    x=intraday_research_decision(30,True,False,"NONE",0,True,.10,True)
    assert x["decision"]=="NO_TRADE_DIRECTION"

def test_intraday_valid_down_candidate():
    x=intraday_research_decision(30,True,True,"DOWN",-.06,True,.12,True)
    assert x["decision"]=="RESEARCH_PUT_CANDIDATE"
def test_scoreboard(tmp_path):
    p=tmp_path/"x.csv";out=tmp_path/"s.json"
    rows=[
      {"symbol":"SPY","call_terminal_return_30m":"0.2","put_terminal_return_30m":"-0.1","call_30m_tp10_sl10":"TP_FIRST"},
      {"symbol":"SPY","call_terminal_return_30m":"-0.1","put_terminal_return_30m":"0.15","call_30m_tp10_sl10":"SL_FIRST"},
    ]
    fields=sorted({k for r in rows for k in r})
    with open(p,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    s=build_scoreboard(p,out)
    assert s["SPY"]["horizons"]["30"]["call"]["n"]==2
    assert abs(s["SPY"]["horizons"]["30"]["call"]["win_rate"]-.5)<1e-12

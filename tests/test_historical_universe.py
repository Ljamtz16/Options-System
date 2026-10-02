from datetime import date
from src.options_system.historical_universe import build_universe

def c(sym,t,k,e):
    return {"symbol":sym,"type":t,"strike_price":str(k),"expiration_date":e}

def test_universe_is_bounded_by_dte_and_moneyness():
    d=date(2026,9,29)
    xs=[c("A","call",100,"2026-09-30"),c("B","put",104,"2026-10-09"),
        c("C","call",105,"2026-10-02"),c("D","put",100,"2026-10-10")]
    rows=build_universe(xs,d,100)
    assert [r["option_symbol"] for r in rows]==["A","B"]

def test_no_outcome_fields_are_used():
    d=date(2026,9,29)
    x=c("A","call",100,"2026-09-30")
    x.update({"close_price":999,"open_interest":999999,"status":"inactive"})
    assert len(build_universe([x],d,100))==1

from options_system.multisymbol_arbitration import aggregate_multisymbol_signals


def test_exact_same_snapshot_symbol_side_collapses_to_one_opportunity():
    rows = [
        {"captured_at_utc": "2026-10-15T14:00:00+00:00", "decision_date": "2026-10-15", "symbol": "META", "side": "CALL", "candidate_id": "MS02", "contract": "META_CALL"},
        {"captured_at_utc": "2026-10-15T14:00:00+00:00", "decision_date": "2026-10-15", "symbol": "META", "side": "CALL", "candidate_id": "MS04", "contract": "META_CALL"},
        {"captured_at_utc": "2026-10-15T14:00:00+00:00", "decision_date": "2026-10-15", "symbol": "AAPL", "side": "PUT", "candidate_id": "MS01", "contract": "AAPL_PUT"},
    ]
    out = aggregate_multisymbol_signals(rows)
    assert out["raw_signals"] == 3
    assert out["opportunities"] == 2
    assert out["duplicates_collapsed"] == 1
    meta = [x for x in out["rows"] if x["symbol"] == "META"][0]
    assert meta["support_count"] == 2
    assert meta["candidate_ids"] == ["MS02", "MS04"]
    assert meta["broker_order"] is False

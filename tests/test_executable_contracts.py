from options_system.executable_contracts import select_contract, contracts_from_snapshot

TS='2026-10-07T14:00:00Z'


def contract(**kw):
    row=dict(symbol='SPY261009C00100000',bid=1.45,ask=1.50,timestamp=TS,
             bid_size=10,ask_size=10,volume=100,delta=.50)
    row.update(kw);return row


def select(rows, **kw):
    return select_contract(rows,'CALL',TS,100.,1000.,.20,**kw)


def test_budget_searches_whole_chain_and_skips_expensive_delta_target():
    expensive=contract(ask=2.5,bid=2.45)
    affordable=contract(symbol='SPY261009C00101000',delta=.45)
    r=select([expensive,affordable])
    assert r['selected']['symbol']==affordable['symbol']
    assert r['rejected']['INSUFFICIENT_PREMIUM_BUDGET']==1


def test_dte_size_and_bad_delta_block_instead_of_cheap_otm_selection():
    for row in [contract(symbol='SPY261007C00100000'),contract(bid_size=0),contract(delta=.05)]:
        assert select([row])['selected'] is None


def test_atm_fallback_only_when_delta_missing():
    assert select([contract(delta=None)])['selected']['selection_basis']=='ATM_FALLBACK'
    assert select([contract(symbol='SPY261009C00110000',delta=None)])['selected'] is None


def test_future_stale_missing_liquidity_and_nonfinite_quotes_block():
    for row in [contract(timestamp='2026-10-07T14:01:00Z'),contract(timestamp='2026-10-07T13:57:00Z'),
                contract(ask_size=None),contract(volume=None),contract(ask=float('nan'))]:
        assert select([row])['selected'] is None


def test_zero_fraction_blocks_and_put_delta_must_be_negative():
    assert select_contract([contract()],'CALL',TS,100,1000,0)['selected'] is None
    row=contract(symbol='SPY261009P00100000',delta=-.5)
    assert select_contract([row],'PUT',TS,100,1000,.2)['selected'] is not None
    row['delta']=.5
    assert select_contract([row],'PUT',TS,100,1000,.2)['selected'] is None


def test_liquidity_matches_quantity_and_exact_budget_boundary():
    assert select([contract(bid=1.95,ask=2.)])['selected']['premium_cost']==200.
    assert select([contract(ask=2.01,bid=1.99)])['selected'] is None
    assert select([contract(ask=.5,bid=.49,bid_size=1)],quantity=2)['selected'] is None


def test_future_spot_and_volume_are_not_used():
    snap={'captured_at_utc':TS,'payload':{'underlying':{'snapshot':{'latestTrade':{'p':100,'t':'2026-10-07T14:01:00Z'}}},
          'options':{'snapshot':{'snapshots':{'SPY261009C00100000':{'dailyBar':{'v':200,'t':'2026-10-07T14:01:00Z'}}}}}}}
    rows,spot=contracts_from_snapshot(snap)
    assert spot is None and rows[0]['volume'] is None


def test_early_close_blocks_new_signals():
    from options_system.executable_contracts import select_signal
    snapshot={'captured_at_utc':'2026-11-27T18:01:00Z',
              'payload':{'market_clock':{'next_close':'2026-11-27T18:00:00Z'}}}
    r=select_signal(snapshot,{'side':'call','contract':'original'},1000,.2)
    assert r['selection']['reason']=='OUTSIDE_SESSION' and r['contract'] is None

import csv
import importlib.util
import json
from pathlib import Path

from options_system import session_cache as cache
from options_system.dashboard_sessions import publish_meta_views, publish_web, scope_meta


def capture(path, stamp, payload):
    path.write_text(json.dumps(dict(captured_at_utc=stamp, payload=payload)))


def test_snapshot_index_reuses_headers_and_keeps_one_payload(tmp_path, monkeypatch):
    a, b = tmp_path/'spy_options_a.json', tmp_path/'spy_options_b.json'
    capture(a, '2026-10-09T01:00:00Z', {'options': [1]})
    capture(b, '2026-10-09T14:00:00Z', {'options': [2]})
    refs = cache.snapshot_refs(tmp_path, 'spy_options_*.json')
    assert [r.day for r in refs] == ['2026-10-08', '2026-10-09']
    assert refs[0].cache is refs[1].cache
    assert refs[0]['payload']['options'] == [1]
    assert refs[1]['payload']['options'] == [2]
    assert refs[0].cache['path'] == b
    original = Path.read_text
    def checked(path, *args, **kwargs):
        assert path not in (a, b), 'Unchanged raw captures must not be parsed again'
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'read_text', checked)
    assert len(cache.snapshot_refs(tmp_path, 'spy_options_*.json')) == 2


def test_changed_snapshot_invalidates_cache_and_invalid_optional(tmp_path):
    path = tmp_path/'spy_options_a.json'
    capture(path, '2026-10-09T14:00:00Z', {'market_date': '2026-10-09'})
    before = cache.fingerprint(cache.snapshot_refs(tmp_path, 'spy_options_*.json'))
    capture(path, '2026-10-10T14:00:00Z', {'market_date': '2026-10-10', 'x': 100})
    refs = cache.snapshot_refs(tmp_path, 'spy_options_*.json')
    assert refs[0].day == '2026-10-10'
    assert cache.fingerprint(refs) != before
    assert cache.fingerprint(refs, 'v1') != cache.fingerprint(refs, 'v2')
    (tmp_path/'spy_options_bad.json').write_text('{')
    assert len(cache.snapshot_refs(tmp_path, 'spy_options_*.json', skip_invalid=True)) == 1


def test_intraday_rebuild_only_changed_day(tmp_path, monkeypatch):
    import options_system.intraday_dataset_v2 as dataset
    raw = tmp_path/'data/raw/intraday'
    raw.mkdir(parents=True)
    for day in ('2026-10-08', '2026-10-09'):
        capture(raw/('intraday_options_'+day+'.json'), day+'T14:00:00Z', {'market_date': day})
    calls = []
    def build(source, target, snapshot_files=None):
        calls.append(target.stem)
        cache.write_csv(target, [dict(market_date=target.stem, source_file=p.name) for p in snapshot_files])
        return len(snapshot_files)
    monkeypatch.setattr(dataset, 'build_intraday_dataset_v2', build)
    assert cache.build_intraday_sessions(tmp_path) == 2
    calls.clear()
    cache.build_intraday_sessions(tmp_path, '2026-10-09')
    assert calls == []
    capture(raw/'intraday_options_new.json', '2026-10-09T14:01:00Z', {'market_date': '2026-10-09'})
    assert cache.build_intraday_sessions(tmp_path, '2026-10-09') == 3
    assert calls == ['2026-10-09']


def test_dashboard_only_today_archive_incremental_empty_next_day(tmp_path, monkeypatch):
    script = Path(__file__).parents[1]/'scripts/build_intraday_dashboard_data.py'
    spec = importlib.util.spec_from_file_location('dashboard_data', script)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    mod.ROOT = tmp_path; mod.A = tmp_path/'artifacts/intraday'
    mod.CURRENT = tmp_path/'data/processed/intraday/intraday_options_v2.csv'
    mod.DISCOVERY = mod.A/'missing.json'
    for day in ('2026-10-08', '2026-10-09'):
        cache.write_csv(mod.CURRENT.parent/'sessions'/(day+'.csv'), [dict(market_date=day, symbol='SPY', spot=100, captured_at_utc=day+'T14:00:00Z')])
    monkeypatch.setattr(mod, 'today', lambda:'2026-10-09')
    mod.build()
    archive = mod.A/'sessions/2026-10-08.json'
    before = archive.stat().st_mtime_ns
    assert {r['decision_date'] for r in json.loads((mod.A/'intraday_dashboard_data.json').read_text())} == {'2026-10-09'}
    mod.build(); assert archive.stat().st_mtime_ns == before
    archive.unlink(); mod.build(); assert archive.exists()
    monkeypatch.setattr(mod, 'today', lambda:'2026-10-10')
    mod.build(); assert json.loads((mod.A/'intraday_dashboard_data.json').read_text()) == []
    publish_web(mod.A, tmp_path/'web', [])
    assert not (tmp_path/'web/sessions/views-cache.json').exists()
    published = tmp_path/'web/sessions/2026-10-08.json'
    assert published.exists()
    assert published.stat().st_mode & 0o777 == 0o644
    published.chmod(0o600)
    publish_web(mod.A, tmp_path/'web', [])
    assert published.stat().st_mode & 0o777 == 0o644


def test_scope_metadata_filters_ledger_keeps_balances_and_caches_closed(tmp_path, monkeypatch):
    import options_system.dashboard_sessions as views
    ledger = [dict(entry_time='2026-10-08T14:00:00Z', status='CLOSED', net_pnl=9), dict(entry_time='2026-10-09T14:00:00Z', status='CLOSED', net_pnl=2)]
    meta = dict(paper_trading=dict(cash=100, live_ledger=ledger), execution_gate=dict(episodes=[dict(decision_date='2026-10-09', execution_gate=dict(status='PASS'))]), entry_controls_analysis=dict(status='READY'))
    scoped = scope_meta(meta, '2026-10-09')
    assert scoped['paper_trading']['cash'] == 100
    assert scoped['paper_trading']['session_realized_net_pnl'] == 2
    assert len(scoped['paper_trading']['live_ledger']) == 1
    assert scoped['execution_gate']['counts'] == {'PASS': 1}
    assert 'entry_controls_analysis' not in scoped
    assert len(meta['paper_trading']['live_ledger']) == 2
    cache.atomic_text(tmp_path/'index.json', json.dumps(dict(sessions=[dict(day='2026-10-08'), dict(day='2026-10-09')])))
    monkeypatch.setattr(views, 'today', lambda:'2026-10-09')
    publish_meta_views(tmp_path, meta)
    before = (tmp_path/'2026-10-08.meta.json').stat().st_mtime_ns
    publish_meta_views(tmp_path, meta)
    assert (tmp_path/'2026-10-08.meta.json').stat().st_mtime_ns == before
    assert json.loads((tmp_path/'analysis.json').read_text())['entry_controls_analysis']['status'] == 'READY'


def test_lazy_paper_replay_matches_eager_result(tmp_path):
    from options_system.prospective_paper_trader import replay_paper_account
    contract = 'SPY261009C00100000'
    eager = []
    for i, bid in enumerate((1.45, 1.8)):
        stamp = f'2026-10-09T14:0{i}:00Z'
        payload = dict(options=dict(snapshot=dict(snapshots={contract: dict(latestQuote=dict(bp=bid,t=stamp))})))
        capture(tmp_path/f'spy_options_{i}.json', stamp, payload)
        eager.append(dict(captured_at_utc=stamp, payload=payload))
    signal = dict(signal_id='one',hypothesis='H01',side='call',horizon_min=60,signal_time='2026-10-09T14:00:00Z',contract=contract,entry_ask=1.5,entry_bid=1.45,entry_bid_size=10,entry_ask_size=10)
    kwargs = dict(policy={'select_executable_contract':False})
    gate = dict(status='ACTIVE',allowed_max_fraction=.2)
    expected = replay_paper_account(eager,[signal],gate,**kwargs)
    actual = replay_paper_account(cache.snapshot_refs(tmp_path,'spy_options_*.json'),[signal],gate,**kwargs)
    assert actual == expected

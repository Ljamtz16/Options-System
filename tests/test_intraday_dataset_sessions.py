import csv
import json

import pytest

from options_system.intraday_dataset_v2 import build_intraday_dataset_v2


def snapshot(day,minute,spot,bid):
    suffix=day.replace("-","")[2:]
    return {
        "captured_at_utc":f"{day}T13:{minute:02d}:00+00:00",
        "payload":{
            "market_date":day,
            "symbols":{"SPY":{
                "spot":spot,
                "option_snapshot":{"snapshots":{
                    f"SPY{suffix}C00100000":{
                        "greeks":{"delta":.51},
                        "latestQuote":{"bp":bid,"ap":bid+.1}},
                    f"SPY{suffix}P00100000":{
                        "greeks":{"delta":-.49},
                        "latestQuote":{"bp":bid,"ap":bid+.1}},
                }},
            }},
        },
    }


def test_sessions_preserve_input_order_and_isolate_future_outcomes(tmp_path):
    # File order deliberately interleaves two market dates.
    values=[
        snapshot("2026-10-05",30,100,1.9),
        snapshot("2026-10-06",30,100,1.9),
        snapshot("2026-10-05",35,101,2.4),
        snapshot("2026-10-06",35,99,1.4),
    ]
    files=[]
    for i,value in enumerate(values):
        p=tmp_path/f"intraday_options_{i:02d}.json"
        p.write_text(json.dumps(value))
        files.append(p.name)
    out=tmp_path/"dataset.csv"
    assert build_intraday_dataset_v2(tmp_path,out)==4
    with out.open(newline="") as fh:
        rows=list(csv.DictReader(fh))
    assert [r["source_file"] for r in rows]==files
    assert float(rows[0]["terminal_return_5m"])==pytest.approx(.01)
    assert float(rows[1]["terminal_return_5m"])==pytest.approx(-.01)
    assert float(rows[0]["call_terminal_return_eod"])==pytest.approx(.2)
    assert float(rows[1]["call_terminal_return_eod"])==pytest.approx(-.3)
    assert rows[2]["terminal_return_eod"]==""
    assert rows[3]["terminal_return_eod"]==""


def test_no_snapshots_does_not_replace_existing_dataset(tmp_path):
    out=tmp_path/"dataset.csv"
    out.write_text("existing data")
    assert build_intraday_dataset_v2(tmp_path,out)==0
    assert out.read_text()=="existing data"

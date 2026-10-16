from pathlib import Path


def test_fast_tracker_uses_exact_option_quotes():
    root = Path(__file__).resolve().parents[1]

    code = (
        root / "scripts" / "run_fast_paper_tracker.py"
    ).read_text(encoding="utf-8")

    assert "option_latest_quotes" in code
    assert "INTERVAL_SECONDS = 15" in code
    assert "OPEN_PAPER_POSITIONS_ONLY" in code
    assert "return_from_entry" in code
    assert '"TP10"' in code
    assert '"SL10"' in code


def test_latest_option_quote_client_exists():
    root = Path(__file__).resolve().parents[1]

    code = (
        root / "src/options_system/prospective_collector.py"
    ).read_text(encoding="utf-8")

    assert "def option_latest_quotes(" in code
    assert "/v1beta1/options/quotes/latest" in code

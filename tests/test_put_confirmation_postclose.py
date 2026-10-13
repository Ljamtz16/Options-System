from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_put_confirmation_shadow_runs_after_frozen_tracker():
    code = (
        ROOT / "scripts/vps_postclose.py"
    ).read_text(encoding="utf-8")

    frozen = '"scripts/track_frozen_hypotheses.py"'
    put_shadow = '"scripts/track_put_confirmation_shadow_v02.py"'
    report = '"scripts/hypothesis_daily_report.py"'

    assert frozen in code
    assert put_shadow in code
    assert report in code

    assert code.index(frozen) < code.index(put_shadow)
    assert code.index(put_shadow) < code.index(report)

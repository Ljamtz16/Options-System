import json
from datetime import datetime, timezone
from pathlib import Path


def _load(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {} if default is None else default


def _snapshot_time(path):
    data = _load(path, {})
    value = data.get("captured_at_utc")
    if not value:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def build_health(root, now=None):
    root = Path(root)
    now = now or datetime.now(timezone.utc)
    a = root / "artifacts" / "intraday"

    freeze = _load(a / "FROZEN_HYPOTHESES_V02.json", {})
    gate = _load(a / "PROSPECTIVE_RISK_GATE_V01.json", {})
    execution = _load(a / "PROSPECTIVE_EXECUTION_GATE_V01.json", {})
    report = _load(a / "HYPOTHESIS_DAILY_REPORT_V02.json", {})

    raw = root / "data" / "raw" / "prospective"
    snaps = sorted(raw.glob("spy_options_*.json")) if raw.exists() else []

    snapshot_times = [t for t in (_snapshot_time(p) for p in snaps) if t is not None]
    latest = max(snapshot_times) if snapshot_times else None

    h03 = next(
        (
            h
            for h in freeze.get("hypotheses", [])
            if h.get("id") == "H03_CALL_RELATIVE_WEAKNESS_REVERSAL_V01"
        ),
        None,
    )

    start = (h03 or {}).get("prospective_start_after")

    freeze_date = None
    if start:
        try:
            freeze_date = datetime.fromisoformat(start).date()
        except ValueError:
            freeze_date = None

    post_freeze_times = (
        [t for t in snapshot_times if freeze_date and t.date() > freeze_date]
        if freeze_date
        else []
    )

    post_freeze_snapshot_count = len(post_freeze_times)
    latest_post_freeze = max(post_freeze_times) if post_freeze_times else None

    episodes = report.get("prospective_episodes", [])
    dates = sorted(
        {
            e.get("decision_date")
            for e in episodes
            if e.get("decision_date")
        }
    )

    counts = execution.get("counts") or {
        "PASS": 0,
        "BLOCK": 0,
        "REVIEW_MISSING_MARKET_QUALITY": 0,
    }

    if not post_freeze_times:
        evidence_status = "WAITING"
        evidence_detail = "No post-freeze market data received yet"
    elif not dates:
        evidence_status = "NO_SIGNAL"
        evidence_detail = (
            f"{post_freeze_snapshot_count} post-freeze snapshots received; "
            "no H03 episode detected"
        )
    else:
        evidence_status = "PASS"
        evidence_detail = (
            f"{len(episodes)} episodes across {len(dates)} dates; "
            f"{post_freeze_snapshot_count} post-freeze snapshots received"
        )

    checks = [
        {
            "id": "h03_frozen",
            "label": "H03 frozen",
            "status": "PASS" if h03 and start else "FAIL",
            "detail": (
                f"prospective_start_after={start}"
                if start
                else "freeze metadata missing"
            ),
        },
        {
            "id": "raw_snapshots",
            "label": "Raw SPY snapshots",
            "status": "PASS" if snaps else "FAIL",
            "detail": (
                f"{len(snaps)} snapshots; "
                f"latest={latest.isoformat() if latest else '--'}"
            ),
        },
        {
            "id": "prospective_evidence",
            "label": "Prospective evidence",
            "status": evidence_status,
            "detail": evidence_detail,
        },
        {
            "id": "risk_gate",
            "label": "Risk gate",
            "status": (
                "PASS"
                if gate.get("status") in ("ACTIVE", "BLOCKED")
                else "FAIL"
            ),
            "detail": (
                f"{gate.get('status', 'UNKNOWN')} / "
                f"max={gate.get('allowed_max_fraction', 0):.0%}"
            ),
        },
        {
            "id": "execution_gate",
            "label": "Execution gate",
            "status": "PASS" if execution.get("counts") is not None else "FAIL",
            "detail": (
                f"PASS={counts['PASS']} "
                f"BLOCK={counts['BLOCK']} "
                f"REVIEW={counts['REVIEW_MISSING_MARKET_QUALITY']}"
            ),
        },
        {
            "id": "dashboard_meta",
            "label": "Dashboard metadata",
            "status": (
                "PASS"
                if (a / "research_dashboard_meta.json").exists()
                else "FAIL"
            ),
            "detail": (
                "research_dashboard_meta.json present"
                if (a / "research_dashboard_meta.json").exists()
                else "missing"
            ),
        },
    ]

    failures = sum(x["status"] == "FAIL" for x in checks)
    waiting = sum(x["status"] == "WAITING" for x in checks)

    if failures:
        overall = "NOT_READY"
    elif waiting:
        overall = "WAITING_MARKET_DATA"
    elif evidence_status == "NO_SIGNAL":
        overall = "DATA_RECEIVED_NO_SIGNAL"
    else:
        overall = "READY"

    return {
        "version": "v0.2",
        "generated_at_utc": now.isoformat(),
        "overall_status": overall,
        "failures": failures,
        "waiting": waiting,
        "snapshot_count": len(snaps),
        "latest_snapshot_utc": latest.isoformat() if latest else None,
        "post_freeze_snapshot_count": post_freeze_snapshot_count,
        "latest_post_freeze_snapshot_utc": (
            latest_post_freeze.isoformat() if latest_post_freeze else None
        ),
        "prospective_episode_count": len(episodes),
        "checks": checks,
        "notes": [
            "System health is operational readiness, not scientific evidence.",
            "Post-freeze market data without an H03 episode is a valid no-signal outcome.",
            "Collector service/timer liveness must be verified on the VPS with systemd; "
            "this artifact verifies persisted outputs, not process state.",
        ],
    }

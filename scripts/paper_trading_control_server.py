import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "artifacts/intraday/PAPER_TRADING_CONTROL_V01.json"

ALLOWED = [0.0, 0.2, 0.4, 0.6, 0.8]


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def default_control():
    return {
        "version": "v0.1",
        "risk_fraction": 0.20,
        "allowed_fractions": ALLOWED,
        "scope": "PAPER_TRADING_ONLY",
        "scientific_risk_gate_unchanged": True,
        "updated_at_utc": utcnow(),
    }


def load_control():
    if CONTROL.exists():
        return json.loads(CONTROL.read_text(encoding="utf-8"))

    d = default_control()
    save_control(d)
    return d


def save_control(data):
    CONTROL.parent.mkdir(parents=True, exist_ok=True)
    tmp = CONTROL.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(CONTROL)


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path != "/control":
            return self.send_json(404, {"error": "not_found"})

        self.send_json(200, load_control())

    def do_POST(self):
        if self.path != "/control":
            return self.send_json(404, {"error": "not_found"})

        try:
            n = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(n) or b"{}")
            value = float(body["risk_fraction"])
        except Exception:
            return self.send_json(400, {"error": "invalid_json_or_fraction"})

        if value not in ALLOWED:
            return self.send_json(
                400,
                {"error": "fraction_not_allowed", "allowed": ALLOWED},
            )

        data = load_control()
        data["risk_fraction"] = value
        data["updated_at_utc"] = utcnow()
        save_control(data)

        self.send_json(200, data)

    def log_message(self, fmt, *args):
        print("PAPER_CONTROL", self.address_string(), fmt % args)


if __name__ == "__main__":
    load_control()
    print("PAPER_CONTROL_SERVER 127.0.0.1:8090")
    ThreadingHTTPServer(("127.0.0.1", 8090), Handler).serve_forever()

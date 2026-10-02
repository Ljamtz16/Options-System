import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL="https://data.alpaca.markets/v1beta1/options"

def credentials_present():
    return bool(os.getenv("APCA_API_KEY_ID") and os.getenv("APCA_API_SECRET_KEY"))

def _headers():
    if not credentials_present():
        raise RuntimeError("Alpaca credentials are not configured.")
    return {"APCA-API-KEY-ID":os.environ["APCA_API_KEY_ID"],
            "APCA-API-SECRET-KEY":os.environ["APCA_API_SECRET_KEY"]}

def fetch_json(path,params):
    url=f"{BASE_URL}/{path}?{urlencode(params)}"
    req=Request(url,headers=_headers(),method="GET")
    with urlopen(req,timeout=30) as response:
        return json.loads(response.read().decode("utf-8")),url

def save_snapshot(payload,request_url,output_path):
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"))
    meta={"retrieved_at_utc":datetime.now(timezone.utc).isoformat(),
          "request_url":request_url,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
    Path(output_path).write_text(json.dumps({"metadata":meta,"payload":payload},indent=2),encoding="utf-8")
    return meta

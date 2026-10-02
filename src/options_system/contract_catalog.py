import json, os
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from .env import load_local_env
BASE="https://paper-api.alpaca.markets"

def fetch_contracts(params):
    load_local_env()
    headers={"APCA-API-KEY-ID":os.environ["APCA_API_KEY_ID"],
             "APCA-API-SECRET-KEY":os.environ["APCA_API_SECRET_KEY"]}
    rows=[]; token=None
    while True:
        q=dict(params)
        if token:q["page_token"]=token
        url=BASE+"/v2/options/contracts?"+urlencode(q)
        with urlopen(Request(url,headers=headers),timeout=30) as r:
            payload=json.loads(r.read().decode())
        rows.extend(payload.get("option_contracts",[]))
        token=payload.get("next_page_token")
        if not token:return rows

def fetch_contracts_all_statuses(params):
    merged={}
    for status in ("active","inactive"):
        q=dict(params); q["status"]=status
        for c in fetch_contracts(q): merged[c["symbol"]]=c
    return list(merged.values())

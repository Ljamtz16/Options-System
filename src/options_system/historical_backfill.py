import json
from pathlib import Path
from .alpaca_history import fetch_json, save_snapshot

def fetch_pages(kind,symbol,start,end,output_dir,timeframe="1Min",resume=True):
    output_dir=Path(output_dir); output_dir.mkdir(parents=True,exist_ok=True)
    checkpoint=output_dir/"checkpoint.json"
    token=None; page=0; total=0; files=[]
    if resume and checkpoint.exists():
        state=json.loads(checkpoint.read_text())
        token=state.get("next_page_token"); page=state.get("pages",0)
        total=state.get("records",0); files=state.get("files",[])
        if state.get("complete"):
            return state["manifest"]
    while True:
        params={"symbols":symbol,"start":start,"end":end,"limit":1000}
        if kind=="bars": params["timeframe"]=timeframe
        if token: params["page_token"]=token
        payload,url=fetch_json(kind,params)
        rows=payload.get(kind,{}).get(symbol,[])
        page+=1; total+=len(rows)
        out=output_dir/f"{kind}_page_{page:04d}.json"
        if out.exists(): raise FileExistsError(out)
        meta=save_snapshot(payload,url,out)
        files.append({"page":page,"records":len(rows),"sha256":meta["sha256"],"file":out.name})
        token=payload.get("next_page_token")
        state={"next_page_token":token,"pages":page,"records":total,"files":files,"complete":not bool(token)}
        checkpoint.write_text(json.dumps(state,indent=2),encoding="utf-8")
        if not token: break
    manifest={"symbol":symbol,"kind":kind,"start":start,"end":end,
              "pages":page,"records":total,"files":files}
    m=output_dir/f"{kind}_manifest.json"
    if not m.exists(): m.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    state["manifest"]=manifest; checkpoint.write_text(json.dumps(state,indent=2),encoding="utf-8")
    return manifest

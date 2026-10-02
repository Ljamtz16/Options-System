TOUCH_LEVELS=(0.0025,0.0050)

def path_outcomes(spots,entry_spot):
    if not spots or not entry_spot:return {}
    rets=[float(x)/float(entry_spot)-1 for x in spots]
    out={"mfe":max(rets),"mae":min(rets),
         "terminal_return":rets[-1],"up":rets[-1]>0}
    for level in TOUCH_LEVELS:
        tag=f"{int(level*10000)}bp"
        up_i=next((i for i,r in enumerate(rets) if r>=level),None)
        dn_i=next((i for i,r in enumerate(rets) if r<=-level),None)
        if up_i is None and dn_i is None:touch="NEITHER"
        elif dn_i is None or (up_i is not None and up_i<dn_i):touch="UP"
        elif up_i is None or dn_i<up_i:touch="DOWN"
        else:touch="AMBIGUOUS"
        out[f"first_touch_{tag}"]=touch
        out[f"up_touch_{tag}"]=up_i is not None
        out[f"down_touch_{tag}"]=dn_i is not None
    return out

def contract_path_outcomes(entry,exit_snapshots):
    if not entry:return {}
    bids=[]
    for snap in exit_snapshots:
        s=((snap or {}).get("snapshots") or {}).get(entry["symbol"])
        q=(s or {}).get("latestQuote") or {};b=q.get("bp")
        if b is not None and float(b)>0:bids.append(float(b))
    if not bids:return {}
    ask=float(entry["ask"]);rets=[b/ask-1 for b in bids]
    return {"best_return":max(rets),"worst_return":min(rets),
            "terminal_return":rets[-1],"best_pnl_usd":max(rets)*ask*100,
            "worst_pnl_usd":min(rets)*ask*100}
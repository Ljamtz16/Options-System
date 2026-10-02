TP_LEVELS=(0.10,0.20)
SL_LEVELS=(0.10,0.20)

def option_trade_targets(path_returns,prefix):
    out={}
    for tp in TP_LEVELS:
        for sl in SL_LEVELS:
            tp_i=next((i for i,r in enumerate(path_returns) if r>=tp),None)
            sl_i=next((i for i,r in enumerate(path_returns) if r<=-sl),None)
            if tp_i is None and sl_i is None:res="NEITHER"
            elif sl_i is None or (tp_i is not None and tp_i<sl_i):res="TP_FIRST"
            elif tp_i is None or sl_i<tp_i:res="SL_FIRST"
            else:res="AMBIGUOUS"
            tag=f"tp{int(tp*100)}_sl{int(sl*100)}"
            out[f"{prefix}_{tag}"]=res
    return out

def direct_profit_targets(ret,prefix):
    if ret is None:return {}
    return {f"{prefix}_gt_10pct":ret>=.10,
            f"{prefix}_gt_20pct":ret>=.20,
            f"{prefix}_positive":ret>0}
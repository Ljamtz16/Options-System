import json
from pathlib import Path
sym="SPY260930C00760000"
for name,kind in [("alpaca_spy260930c00760000_bars_probe.json","bars"),("alpaca_spy260930c00760000_trades_probe.json","trades")]:
    d=json.loads((Path("data/raw")/name).read_text())
    obj=d["payload"].get(kind,{})
    rows=obj.get(sym,[]) if isinstance(obj,dict) else obj
    print(name, "records=", len(rows))
    if rows:
        print(" first=", rows[0])
        print(" last=", rows[-1])

from dataclasses import dataclass
@dataclass(frozen=True)
class AssetConfig:
 symbol:str;event_threshold:float;dte_min:int=1;dte_max:int=10;max_spread_pct:float=.20
DEFAULTS={"SPY":AssetConfig("SPY",.01),"QQQ":AssetConfig("QQQ",.0125),"AAPL":AssetConfig("AAPL",.015),
"NVDA":AssetConfig("NVDA",.02),"TSLA":AssetConfig("TSLA",.025)}
def get_asset_config(symbol):
 return DEFAULTS.get(symbol.upper(),AssetConfig(symbol.upper(),.015))

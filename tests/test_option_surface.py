from datetime import date
from options_system.option_surface import extract_option_surface

def test_option_surface_by_dte_delta():
 chain={"snapshots":{
  "SPY261005C00770000":{"impliedVolatility":.20,"latestQuote":{"bp":2.0,"ap":2.2},"dailyBar":{"v":100},"greeks":{"delta":.50}},
  "SPY261005P00770000":{"impliedVolatility":.22,"latestQuote":{"bp":2.1,"ap":2.3},"dailyBar":{"v":120},"greeks":{"delta":-.50}},
  "SPY261005C00780000":{"impliedVolatility":.18,"latestQuote":{"bp":1.0,"ap":1.2},"dailyBar":{"v":80},"greeks":{"delta":.25}},
  "SPY261005P00760000":{"impliedVolatility":.24,"latestQuote":{"bp":1.1,"ap":1.3},"dailyBar":{"v":90},"greeks":{"delta":-.25}}
 }}
 x=extract_option_surface(chain,770,date(2026,10,2))
 assert abs(x["dte_1_3_25d_put_minus_call_iv"]-.06)<1e-12
 assert abs(x["dte_1_3_50d_put_minus_call_iv"]-.02)<1e-12

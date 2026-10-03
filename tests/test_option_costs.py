from options_system.option_costs import one_contract_trade,daily_regulatory_fees

def test_one_contract_uses_observed_ask_bid_path():
 t=one_contract_trade(2.62,0.12213740458015265)
 assert t['capital_required']==262.0
 assert round(t['exit_price'],2)==2.94
 assert round(t['gross_pnl'],2)==32.0

def test_daily_fees_use_alpaca_daily_category_rounding():
 trades=[
  one_contract_trade(e,r) for e,r in [
   (2.62,.12213740458015265),(2.64,.11363636363636354),(2.39,-.10460251046025104),
   (2.15,.1348837209302325),(2.25,.10222222222222221),(2.21,.158371040723982)]]
 f=daily_regulatory_fees(trades)
 assert f['components']=={'ORF':.18,'OCC':.30,'CAT':.01,'TAF':.02,'SEC':.04}
 assert f['total']==.55

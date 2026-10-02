from options_system.cross_market_features import cross_market_features

def snap(price,open_,prev):
 return {"latestTrade":{"p":price},"dailyBar":{"o":open_},"prevDailyBar":{"c":prev}}

def test_cross_market_features():
 x=cross_market_features(snap(101,100,99),snap(202,200,199),snap(50,51,50))
 assert x["spy_from_open"]>0
 assert x["qqq_from_open"]>0
 assert x["iwm_from_open"]<0
 assert x["cross_market_up_count"]==2
 assert x["cross_market_down_count"]==1
 assert "qqq_minus_spy_from_open" in x

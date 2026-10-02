from options_system.sector_breadth import sector_breadth_features
def s(p,o): return {"latestTrade":{"p":p},"dailyBar":{"o":o}}
def test_sector_breadth():
 x=sector_breadth_features({"XLK":s(101,100),"XLF":s(99,100),"XLE":s(102,100),"XLV":s(98,100),"XLI":s(100.5,100)})
 assert x["sector_count"]==5
 assert x["sector_up_count"]==3
 assert x["sector_down_count"]==2

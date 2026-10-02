from options_system.option_math import black_scholes, implied_volatility
spot=(763.96+763.99)/2
strike=765.0
years=(24*60+3)/(365*24*60)
rate=0.04
rows=[("call",2.13,2.14,.1615,.4439,.0612,-1.3109,.1580),
      ("put",2.95,2.96,.1539,-.5590,.0641,-1.1687,.1578)]
for typ,bid,ask,piv,pdelta,pgamma,ptheta,pvega in rows:
    mid=(bid+ask)/2
    iv=implied_volatility(mid,spot,strike,years,rate,typ)
    g=black_scholes(spot,strike,years,rate,iv,typ)
    print(typ,"mid",mid,"derived_iv",round(iv,6),"provider_iv",piv)
    print("delta",round(g["delta"],4),pdelta,"gamma",round(g["gamma"],4),pgamma)
    print("theta",round(g["theta_per_day"],4),ptheta,"vega",round(g["vega_per_1pct"],4),pvega)

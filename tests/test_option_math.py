from src.options_system.option_math import black_scholes, implied_volatility

def test_call_put_parity():
    s,k,t,r,v=100,100,30/365,0.04,0.20
    c=black_scholes(s,k,t,r,v,"call")["price"]
    p=black_scholes(s,k,t,r,v,"put")["price"]
    assert abs((c-p)-(s-k*__import__("math").exp(-r*t))) < 1e-8

def test_iv_round_trip_call():
    args=(100,105,45/365,0.03,0.27,"call")
    price=black_scholes(*args)["price"]
    iv=implied_volatility(price,args[0],args[1],args[2],args[3],args[5])
    assert abs(iv-args[4]) < 1e-5

def test_iv_round_trip_put():
    args=(100,95,20/365,0.03,0.33,"put")
    price=black_scholes(*args)["price"]
    iv=implied_volatility(price,args[0],args[1],args[2],args[3],args[5])
    assert abs(iv-args[4]) < 1e-5

def test_greeks_have_expected_signs():
    c=black_scholes(100,100,30/365,0.04,0.2,"call")
    p=black_scholes(100,100,30/365,0.04,0.2,"put")
    assert c["delta"] > 0 and p["delta"] < 0
    assert c["gamma"] > 0 and p["gamma"] > 0
    assert c["vega_per_1pct"] > 0 and p["vega_per_1pct"] > 0

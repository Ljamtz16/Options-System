import math

def _norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def _norm_pdf(x):
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)

def black_scholes(spot, strike, years, rate, sigma, option_type):
    if min(spot, strike, years, sigma) <= 0:
        raise ValueError("spot, strike, years and sigma must be positive")
    root_t = math.sqrt(years)
    d1 = (math.log(spot / strike) + (rate + 0.5*sigma*sigma)*years) / (sigma*root_t)
    d2 = d1 - sigma*root_t
    disc = math.exp(-rate*years)
    if option_type == "call":
        price = spot*_norm_cdf(d1) - strike*disc*_norm_cdf(d2)
        delta = _norm_cdf(d1)
        theta = -(spot*_norm_pdf(d1)*sigma)/(2*root_t) - rate*strike*disc*_norm_cdf(d2)
    elif option_type == "put":
        price = strike*disc*_norm_cdf(-d2) - spot*_norm_cdf(-d1)
        delta = _norm_cdf(d1) - 1
        theta = -(spot*_norm_pdf(d1)*sigma)/(2*root_t) + rate*strike*disc*_norm_cdf(-d2)
    else:
        raise ValueError("option_type must be call or put")
    gamma = _norm_pdf(d1)/(spot*sigma*root_t)
    vega = spot*_norm_pdf(d1)*root_t
    return {"price":price,"delta":delta,"gamma":gamma,"theta_per_day":theta/365.0,"vega_per_1pct":vega/100.0}

def implied_volatility(price, spot, strike, years, rate, option_type, tol=1e-7):
    lo, hi = 1e-6, 5.0
    plo = black_scholes(spot,strike,years,rate,lo,option_type)["price"]
    phi = black_scholes(spot,strike,years,rate,hi,option_type)["price"]
    if not (plo <= price <= phi):
        return None
    for _ in range(100):
        mid=(lo+hi)/2
        pm=black_scholes(spot,strike,years,rate,mid,option_type)["price"]
        if abs(pm-price) <= tol:
            return mid
        if pm < price: lo=mid
        else: hi=mid
    return (lo+hi)/2

from datetime import date, timedelta

DTE_MIN=1
DTE_MAX=10
WIDTH_PCT=0.04

def eligible_contract(contract, session_date, spot):
    exp=date.fromisoformat(contract["expiration_date"])
    dte=(exp-session_date).days
    strike=float(contract["strike_price"])
    ctype=contract["type"].lower()
    return (ctype in {"call","put"} and DTE_MIN <= dte <= DTE_MAX
            and spot*(1-WIDTH_PCT) <= strike <= spot*(1+WIDTH_PCT))

def build_universe(contracts, session_date, spot):
    rows=[]
    for c in contracts:
        if eligible_contract(c,session_date,spot):
            exp=date.fromisoformat(c["expiration_date"])
            strike=float(c["strike_price"])
            rows.append({"session_date":session_date.isoformat(),
                         "option_symbol":c["symbol"],"option_type":c["type"].lower(),
                         "strike":strike,"expiration_date":c["expiration_date"],
                         "dte":(exp-session_date).days,
                         "spot_reference":float(spot),
                         "moneyness":strike/float(spot)-1.0})
    return sorted(rows,key=lambda x:(x["expiration_date"],x["strike"],x["option_type"]))

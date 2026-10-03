from decimal import Decimal, ROUND_CEILING

# Alpaca Securities Brokerage Fee Schedule, revised 2026-09-17.
SEC_RATE = Decimal('0.0000206')       # sell-side trade value
TAF_PER_CONTRACT = Decimal('0.00329') # sell only
CAT_PER_EQ_SHARE = Decimal('0.000003')# buy and sell; option multiplier 100
ORF_PER_CONTRACT = Decimal('0.015')   # buy and sell
OCC_PER_CONTRACT = Decimal('0.025')   # buy and sell
MULTIPLIER = Decimal('100')

def one_contract_trade(entry_ask, exit_return, extra_slippage_cents_per_leg=0):
    if entry_ask in (None, '') or exit_return in (None, ''):
        return None
    entry=Decimal(str(entry_ask)); ret=Decimal(str(exit_return))
    exit_price=entry*(Decimal('1')+ret)
    capital=entry*MULTIPLIER
    gross=(exit_price-entry)*MULTIPLIER
    # Spread is already embedded: entry uses ask and exit path uses bid.
    raw_fees=(ORF_PER_CONTRACT+OCC_PER_CONTRACT+CAT_PER_EQ_SHARE*MULTIPLIER)*2
    raw_fees+=TAF_PER_CONTRACT+SEC_RATE*(exit_price*MULTIPLIER)
    slippage=Decimal(str(extra_slippage_cents_per_leg))/Decimal('100')*MULTIPLIER*2
    return {'entry_price':float(entry),'exit_price':float(exit_price),'capital_required':float(capital),
            'gross_pnl':float(gross),'raw_regulatory_fees':float(raw_fees),
            'extra_slippage':float(slippage),'net_pnl_before_daily_rounding':float(gross-raw_fees-slippage)}

def daily_regulatory_fees(trades):
    valid=[t for t in trades if t]
    n=Decimal(len(valid)); sell_value=sum((Decimal(str(t['exit_price']))*MULTIPLIER for t in valid),Decimal('0'))
    raw={'ORF':ORF_PER_CONTRACT*n*2,'OCC':OCC_PER_CONTRACT*n*2,
         'CAT':CAT_PER_EQ_SHARE*MULTIPLIER*n*2,'TAF':TAF_PER_CONTRACT*n,'SEC':SEC_RATE*sell_value}
    rounded={k:v.quantize(Decimal('0.01'),rounding=ROUND_CEILING) for k,v in raw.items()}
    return {'components':{k:float(v) for k,v in rounded.items()},'total':float(sum(rounded.values(),Decimal('0')))}

from dataclasses import dataclass
@dataclass(frozen=True)
class ExecutionQuote:
 bid:float; ask:float
 def valid(self):return self.bid>=0 and self.ask>0 and self.ask>=self.bid
 @property
 def mid(self):return (self.bid+self.ask)/2 if self.valid() else None
 @property
 def spread(self):return self.ask-self.bid if self.valid() else None
def entry_price_long(q,slippage_fraction=.25):
 if not q.valid():raise ValueError("invalid quote")
 return min(q.ask,q.mid+q.spread*slippage_fraction)
def exit_price_long(q,slippage_fraction=.25):
 if not q.valid():raise ValueError("invalid quote")
 return max(q.bid,q.mid-q.spread*slippage_fraction)
def round_trip_execution_cost(entry_quote,exit_quote,multiplier=100,slippage_fraction=.25,fees=0):
 e=entry_price_long(entry_quote,slippage_fraction);x=exit_price_long(exit_quote,slippage_fraction)
 return {"entry_fill":e,"exit_fill":x,"execution_drag":((e-entry_quote.mid)+(exit_quote.mid-x))*multiplier+fees}

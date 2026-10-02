from src.options_system.contract_quality import quality_flags,research_eligible
def test_good_contract():
 r={"dte":5,"bid":2,"ask":2.1,"iv":.2,"sample_n":200};assert research_eligible(r)
def test_bad_quote_and_iv():
 r={"dte":5,"bid":0,"ask":0,"iv":None,"sample_n":200};f=quality_flags(r);assert "INVALID_QUOTE" in f and "MISSING_IV" in f
def test_wide_spread():
 r={"dte":5,"bid":1,"ask":2,"iv":.2,"sample_n":200};assert "WIDE_SPREAD" in quality_flags(r)

def iv_scenarios(base_iv,shock_abs=.03):
 if base_iv<=0:raise ValueError("base_iv")
 return {"crush":max(1e-6,base_iv-shock_abs),"unchanged":base_iv,"expansion":base_iv+shock_abs}
def conservative_iv_for_long(option_type,base_iv,shock_abs=.03):
 return max(1e-6,base_iv-shock_abs)

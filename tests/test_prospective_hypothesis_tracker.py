from options_system.prospective_hypothesis_tracker import hypothesis_active,summarize

def test_call_hypothesis_exact_rules():
 h={'id':'CALL_FLOW_REVERSAL_V01','side':'call','horizon_min':60,'rules':{
   'd_atm_iv_prev_gt':0.0,'d_put_call_iv_skew_prev_lt':0.0,
   'd_put_call_volume_ratio_1pct_prev_gt':0.0}}
 row={'d_atm_iv_prev':'0.001','d_put_call_iv_skew_prev':'-0.001',
      'd_put_call_volume_ratio_1pct_prev':'0.02'}
 assert hypothesis_active(h,row)
 row['d_put_call_iv_skew_prev']='0.001'
 assert not hypothesis_active(h,row)

def test_put_hypothesis_exact_rules():
 h={'id':'PUT_SKEW_SHORT_V01','side':'put','horizon_min':15,'rules':{
   'put_call_iv_skew_gt':0.0045,'put_call_volume_ratio_1pct_lt':1.05}}
 assert hypothesis_active(h,{'put_call_iv_skew':'0.005','put_call_volume_ratio_1pct':'1.0'})
 assert not hypothesis_active(h,{'put_call_iv_skew':'0.004','put_call_volume_ratio_1pct':'1.0'})

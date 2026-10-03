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


def test_summarize_path_metrics_and_tp_before_sl():
 h={'id':'H','side':'call','horizon_min':60,'rules':{}}
 rows=[{'active_hypotheses':'H','call_ret_60m':'0.05','call_mfe_60m':'0.20',
        'call_mae_60m':'-0.12','call_60m_tp10_sl10':'TP_FIRST'},
       {'active_hypotheses':'H','call_ret_60m':'-0.02','call_mfe_60m':'0.04',
        'call_mae_60m':'-0.15','call_60m_tp10_sl10':'SL_FIRST'}]
 x=summarize(rows,[h])['H']
 assert x['n']==2
 assert abs(x['mean_mfe']-0.12)<1e-12
 assert abs(x['mean_mae']+0.135)<1e-12
 assert x['tp10_before_sl10_rate']==0.5
 assert x['tp10_sl10_decided_n']==2

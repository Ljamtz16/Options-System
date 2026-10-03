from options_system.feature_lab_scan import scan_univariate

def test_scan_excludes_outcome_leakage_and_deduplicates():
 rows=[]
 for i in range(20):
  rows.append({'x':str(i),'call_ret_60m':str(i),'label_call_mfe10_60m':'1' if i>=15 else '0'})
 z=scan_univariate(rows,'label_call_mfe10_60m',min_n=5)
 assert z
 assert all(x['feature']!='call_ret_60m' for x in z)
 keys={(x['feature'],x['op'],round(x['threshold'],12)) for x in z}
 assert len(keys)==len(z)

def test_scan_excludes_prior_model_outputs():
 rows=[]
 for i in range(20):
  y='1' if i>=15 else '0'
  rows.append({'x':str(i),'p_raw':str(i),'p_calibrated':str(i),'o6_decision':str(i),'model_score':str(i),'label_call_mfe10_60m':y})
 z=scan_univariate(rows,'label_call_mfe10_60m',min_n=5)
 assert z
 banned={'p_raw','p_calibrated','o6_decision','model_score'}
 assert not ({x['feature'] for x in z}&banned)

from options_system.prospective_governance import canonical_hash,daily_rows,scoreboard,session_manifest

H=[{'id':'H','side':'call','horizon_min':60,'rules':{'x':1}}]
META={'version':'v0.1','frozen_at':'2026-10-02','hypotheses':H}

def test_hash_is_order_stable():
 assert canonical_hash([{'b':2,'a':1}])==canonical_hash([{'a':1,'b':2}])

def test_daily_excludes_freeze_day_and_aggregates():
 rows=[{'decision_date':'2026-10-02','active_hypotheses':'H','call_ret_60m':'1'},
       {'decision_date':'2026-10-05','captured_at_utc':'t1','active_hypotheses':'H',
        'call_ret_60m':'0.2','call_mfe_60m':'0.3','call_mae_60m':'-0.1',
        'call_60m_tp10_sl10':'TP_FIRST'}]
 x=daily_rows(rows,H,'2026-10-02')
 assert len(x)==1 and x[0]['decision_date']=='2026-10-05'
 assert x[0]['n_signals']==1 and x[0]['daily_result']=='POSITIVE'

def test_scoreboard_gates_by_independent_days():
 daily=[{'decision_date':'2026-10-05','hypothesis':'H','activated':True,'n_signals':3,
         'mean_return':0.1,'tp_first':2,'sl_first':1}]
 x=scoreboard(daily,H)['H']
 assert x['prospective_days']==1 and x['activations']==3
 assert x['status']=='INSUFFICIENT_SAMPLE' and x['next_review_day']==5

def test_manifest_binds_frozen_hypotheses():
 m=session_manifest(META,'2026-10-05',[{'captured_at_utc':'t','call_contract':'X'}])
 assert m['hypothesis_version']=='v0.1'
 assert len(m['hypotheses_sha256'])==64 and m['contracts']==['X']

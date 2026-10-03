from options_system.candidate_hypotheses import candidate_active
from options_system.episode_evaluation import evaluate_candidate_days

def test_discovery_day_is_excluded():
    c={'id':'X','side':'call','horizon_min':60,'rules':[{'feature':'x','op':'<=','value':1}]}
    assert candidate_active(c,{'x':'1'})
    rows=[
      {'captured_at_utc':'2026-10-02T15:00:00+00:00','decision_date':'2026-10-02','x':1,'call_60m_tp10_sl10':'TP_FIRST'},
      {'captured_at_utc':'2026-10-03T15:00:00+00:00','decision_date':'2026-10-03','x':1,'call_60m_tp10_sl10':'TP_FIRST'},
      {'captured_at_utc':'2026-10-03T15:20:00+00:00','decision_date':'2026-10-03','x':1,'call_60m_tp10_sl10':'SL_FIRST'}]
    days=evaluate_candidate_days(rows,c)
    assert len(days)==1
    assert days[0]['episodes']==2
    assert days[0]['tp_first']==1

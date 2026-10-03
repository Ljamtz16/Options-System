from options_system.intraday_episodes import group_episodes,summarize_episodes

def test_groups_by_time_gap_and_uses_first_activation():
 rows=[
  {'captured_at_utc':'2026-10-02T14:00:00+00:00','h03':True,'call_contract':'A','call_entry_ask':2,'call_ret_60m':.2,'call_mfe_60m':.3,'call_mae_60m':-.1,'call_60m_tp10_sl10':'TP_FIRST'},
  {'captured_at_utc':'2026-10-02T14:05:00+00:00','h03':True,'call_contract':'B','call_60m_tp10_sl10':'SL_FIRST'},
  {'captured_at_utc':'2026-10-02T14:20:00+00:00','h03':True,'call_contract':'C','call_60m_tp10_sl10':'SL_FIRST'}]
 e=group_episodes(rows,max_gap_minutes=6)
 assert len(e)==2 and len(e[0]['rows'])==2
 s=summarize_episodes(rows,max_gap_minutes=6)
 assert s[0]['contract']=='A' and s[0]['tp_before_sl']==1
 assert s[1]['contract']=='C' and s[1]['tp_before_sl']==0

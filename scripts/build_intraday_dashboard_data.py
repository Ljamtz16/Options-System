import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader(open(R/'data/processed/intraday/intraday_feature_lab_v01.csv',encoding='utf-8')))
def f(x):
 try:return float(x)
 except:return None
def h03(r):
 a,b=f(r.get('iwm_from_open')),f(r.get('spy_from_open'))
 return a is not None and b is not None and a<=-0.003338055604745982 and b<=-0.002140966419266088
keep=['captured_at_utc','decision_date','spot','spy_from_open','iwm_from_open','qqq_from_open','atm_iv','put_call_iv_skew','put_call_volume_ratio_1pct','call_contract','call_entry_ask','call_ret_60m','call_mfe_60m','call_mae_60m','call_60m_tp10_sl10','put_contract','put_entry_ask','put_ret_15m','put_mfe_15m','put_mae_15m','put_15m_tp10_sl10']
data=[]
for r in rows:
 x={k:r.get(k) for k in keep};x['h03']=h03(r);data.append(x)
out=R/'artifacts/intraday/intraday_dashboard_data.json'
raw=json.dumps(data,separators=(',',':'))
out.write_text(raw,encoding='utf-8')
js=R/'artifacts/intraday/intraday_dashboard_data.js'
js.write_text('window.DASHBOARD_DATA='+raw+';',encoding='utf-8')
print('DASHBOARD_DATA_OK',len(data),out,js)

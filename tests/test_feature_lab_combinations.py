from options_system.feature_lab_combinations import scan_combinations

def test_combination_support():
    rows=[{'captured_at_utc':str(i),'a':str(i%10),'b':str((i//2)%10),'spot':str(700+i),'label_call_tp10_before_sl10_60m':str(int(i%10>=7))} for i in range(40)]
    found=scan_combinations(rows,'label_call_tp10_before_sl10_60m',min_n=4,top_features=5,max_rules=2)
    assert all(x['n']>=4 for x in found)
    assert all(rule['feature']!='spot' for x in found for rule in x['rules'])

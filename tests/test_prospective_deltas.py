from options_system.prospective_dataset import add_snapshot_deltas
def test_snapshot_deltas_do_not_cross_days():
 rows=[
  {"captured_at_utc":"2026-10-02T15:00:00+00:00","decision_date":"2026-10-02","spot":100,"atm_iv":.20},
  {"captured_at_utc":"2026-10-02T15:05:00+00:00","decision_date":"2026-10-02","spot":101,"atm_iv":.22},
  {"captured_at_utc":"2026-10-05T15:00:00+00:00","decision_date":"2026-10-05","spot":110,"atm_iv":.25}]
 x=add_snapshot_deltas(rows)
 assert x[1]["d_spot_prev"]==1
 assert abs(x[1]["d_atm_iv_prev"]-.02)<1e-12
 assert x[1]["minutes_since_prev"]==5
 assert x[2]["d_spot_prev"] is None
 assert x[2]["d_spot_since_first"]==0

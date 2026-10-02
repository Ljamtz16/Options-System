from src.options_system.temporal_protocol import add_label_end_dates,temporal_split
def test_split_keeps_old_training_data():
 rows=[{"date":f"{y}-01-01"} for y in range(2016,2024)]
 x=add_label_end_dates(rows,(1,))
 s=temporal_split(x,"2019-12-31","2021-12-31",1)
 assert [r["date"] for r in s["train"]]==["2016-01-01","2017-01-01","2018-01-01"]
 assert [r["date"] for r in s["validation"]]==["2020-01-01"]

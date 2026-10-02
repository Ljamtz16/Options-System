from src.options_system.temporal_protocol import add_label_end_dates,temporal_split
def test_purge_uses_label_end():
 rows=[{"date":f"2024-01-{i:02d}"} for i in range(1,21)]
 x=add_label_end_dates(rows,(3,))
 s=temporal_split(x,"2024-01-10","2024-01-16",3)
 assert s["train"][-1]["date"]=="2024-01-07"
 assert s["validation"][-1]["date"]=="2024-01-13"
 assert all(r["label_end_h3"]<="2024-01-10" for r in s["train"])
 assert all(r["label_end_h3"]<="2024-01-16" for r in s["validation"])

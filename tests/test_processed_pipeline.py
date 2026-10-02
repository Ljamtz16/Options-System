import json
from src.options_system.processed_pipeline import process_month
def test_failed_session_not_normalized(tmp_path):
 raw=tmp_path/"raw"/"M"/"D";raw.mkdir(parents=True); mans=tmp_path/"mans"/"M"/"D";mans.mkdir(parents=True)
 (raw/"batch_0000_page_0001.json").write_text(json.dumps({"payload":{"bars":{}}}))
 (mans/"universe.json").write_text(json.dumps({"universe":[{"option_symbol":"X"}]}))
 s=process_month("M",tmp_path/"raw",tmp_path/"mans",tmp_path/"out")
 assert s["fail"]==1 and s["processed_rows"]==0 and not (tmp_path/"out"/"M"/"D.csv").exists()

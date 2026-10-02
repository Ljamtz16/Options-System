from options_system.env import load_local_env
load_local_env()
from options_system.multimonth_orchestrator import run_month
rows=run_month(2024,3,"data/raw/historical/downloader_v1","data/raw/historical/manifests_v1")
print("MARCH_DONE sessions=",len(rows),flush=True)

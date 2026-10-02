from options_system.env import load_local_env
from options_system.multimonth_orchestrator import run_month
load_local_env()
rows=run_month(2024,4,"data/raw/historical/downloader_v1","data/raw/historical/manifests_v1")
print("APRIL_DOWNLOAD_DONE",len(rows),flush=True)

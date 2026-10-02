import sys,json
from options_system.processed_pipeline import process_month
s=process_month(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4])
print(json.dumps({k:v for k,v in s.items() if k!="sessions_detail"},indent=2))

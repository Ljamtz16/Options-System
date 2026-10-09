from pathlib import Path
import os
from options_system.session_cache import build_intraday_sessions, today
root=Path(__file__).resolve().parents[1]
day=today() if os.getenv("OPTIONS_BUILD_SCOPE")=="today" else None
n=build_intraday_sessions(root,day)
print(f"BUILT_INTRADAY_V2 rows={n} scope={day or 'changed_sessions'}")

"""Create a new local paper epoch while retaining the complete previous state."""
import argparse
import json
from pathlib import Path
from options_system.paper_epochs import reset_epoch

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--epoch-id',required=True)
    parser.add_argument('--cash',type=float,default=1000.)
    args=parser.parse_args();state=reset_epoch(args.root,args.epoch_id,args.cash)
    print(json.dumps({k:state.get(k) for k in ('epoch_id','epoch_start_utc','cash','equity','paper_risk_fraction',
                                            'previous_epoch_archive','closed_live_trades','last_processed_snapshot_utc')}))

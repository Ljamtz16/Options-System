"""Refresh the independent Jev report without querying Jev or placing orders."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
jev = ROOT.parent / 'jev-lab'
if (jev / 'calibration_analysis.py').exists() and (jev / 'data/lab.sqlite').exists():
    subprocess.run([sys.executable,str(jev/'calibration_analysis.py')],cwd=jev,check=True)
else:
    print('JEV_CALIBRATION_NOT_INSTALLED')

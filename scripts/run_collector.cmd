@echo off
cd /d "D:\Proyectos\Raspberry\Options System"
set "PYTHONPATH=D:\Proyectos\Raspberry\Options System\src"
".venv\Scripts\python.exe" "scripts\collect_spy_options_snapshot.py" >> "artifacts\collector.log" 2>&1

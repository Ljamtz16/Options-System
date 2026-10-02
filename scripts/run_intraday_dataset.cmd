@echo off
cd /d "D:\Proyectos\Raspberry\Options System"
set PYTHONPATH=D:\Proyectos\Raspberry\Options System\src
call .venv\Scripts\python.exe scripts\build_intraday_dataset.py
call .venv\Scripts\python.exe scripts\intraday_daily_report.py
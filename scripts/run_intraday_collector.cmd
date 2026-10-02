@echo off
cd /d "D:\Proyectos\Raspberry\Options System"
set PYTHONPATH=D:\Proyectos\Raspberry\Options System\src
call .venv\Scripts\python.exe scripts\collect_intraday_options_universe.py

@echo off
cd /d "D:\Proyectos\Raspberry\Options System"
set PYTHONPATH=D:\Proyectos\Raspberry\Options System\src
call .venv\Scripts\python.exe scripts\build_prospective_market_state.py
call .venv\Scripts\python.exe scripts\label_prospective_market_state.py

@echo off
cd /d "%~dp0"
python -m pip install --quiet openpyxl
start "" pythonw edit_system_gui.py

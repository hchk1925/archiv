#!/usr/bin/env bash
cd "$(dirname "$0")"
python3 -m pip install --quiet openpyxl 2>/dev/null
python3 edit_system_gui.py
